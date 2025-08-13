from django.shortcuts import render
from datetime import date
from calendar import monthrange
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value, DecimalField
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import SignUpForm, TransactionForm, CategoryForm, AccountForm, BudgetForm, TransferForm
from .models import Transaction, Category, Account, Budget
from django.db.models.deletion import ProtectedError
from django.db.models.functions import TruncDate, Coalesce, Cast
from django.utils import timezone

# ---------- Auth ----------

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # Create starter account & categories
            Account.objects.create(user=user, name='Cash', balance=0)
            Category.objects.get_or_create(user=user, name='Salary', type='income')
            Category.objects.get_or_create(user=user, name='Food', type='expense')
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'auth/signup.html', {'form': form})

# ---------- Dashboard ----------

@login_required
def dashboard(request):
    user = request.user
    today = date.today()
    first_day = today.replace(day=1)
    last_day = today.replace(day=monthrange(today.year, today.month)[1])

    month_tx = Transaction.objects.filter(user=user, date__range=[first_day, last_day])
    income = month_tx.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
    expense = month_tx.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
    net = income - expense
    spent = expense

    # NEW: Live Money = opening balances + all-time income - all-time expense
    opening_sum = Account.objects.filter(user=user).aggregate(total=Sum('balance'))['total'] or Decimal('0')
    all_tx = (
        Transaction.objects
        .filter(user=user)
        .values('type')
        .annotate(total=Sum('amount'))
    )
    in_total = Decimal('0'); out_total = Decimal('0')
    for row in all_tx:
        if row['type'] == 'income':
            in_total += row['total'] or 0
        else:
            out_total += row['total'] or 0
    live_total = Decimal(opening_sum) + in_total - out_total

    # --- Daily expenses for current month ---
    # Month bounds: [start, next_month_start)
    start = date(today.year, today.month, 1)
    next_month_start = date(today.year + (1 if today.month == 12 else 0),
                            1 if today.month == 12 else today.month + 1, 1)

    # Pull only what we need (no DB functions)
    qs = (
        Transaction.objects
        .filter(
            user=user,                      # remove if you don't filter per-user
            type__iexact='expense',
            date__gte=start,
            date__lt=next_month_start,
            date__isnull=False,
        )
        .values_list('date', 'amount')
    )

    # Sum per day in Python (works for DateField or DateTimeField)
    totals_by_day = {}
    for d, amt in qs:
        if d is None:
            continue
        day_num = (d.day if hasattr(d, "day") else int(str(d)[8:10]))  # super defensive
        totals_by_day[day_num] = totals_by_day.get(day_num, 0) + float(amt or 0)

    last_day = (next_month_start - start).days
    exp_daily_labels = [f"{i:02d}" for i in range(1, last_day + 1)]
    exp_daily_values = [totals_by_day.get(i, 0.0) for i in range(1, last_day + 1)]

    # Chart data: last 6 months expense by month
    chart_labels = []
    chart_values = []
    m, y = today.month, today.year
    for _ in range(6):
        chart_labels.append(f"{y}-{m:02d}")
        start = date(y, m, 1)
        end = date(y, m, monthrange(y, m)[1])
        total = Transaction.objects.filter(user=user, type='expense', date__range=[start, end]).aggregate(Sum('amount'))['amount__sum'] or 0
        chart_values.append(float(total))
        # prev month
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    chart_labels.reverse(); chart_values.reverse()

    # Budgets status for this month
    budgets = Budget.objects.filter(user=user, month__year=today.year, month__month=today.month).select_related('category')
    spent_by_cat = (
        month_tx.filter(type='expense')
        .values('category__id', 'category__name')
        .annotate(total=Sum('amount'))
    )
    spent_map = {row['category__id']: row['total'] for row in spent_by_cat}

    live_after_month_expense = Decimal(live_total) - Decimal(expense or 0)
    live_money = live_after_month_expense + income

    budget_labels = [b.category.name for b in budgets]
    budget_values = [float(b.amount or 0) for b in budgets]
    spent_values = [float(spent_map.get(b.category_id, 0) or 0) for b in budgets]
    total=Coalesce(Sum('amount'), Cast(Value(0), DecimalField(max_digits=12, decimal_places=2)))

    accounts = Account.objects.filter(user=request.user).order_by('name')
    # Compute live balances: opening + income - expense per account
    tx = Transaction.objects.filter(user=request.user)
    totals = (
        tx.values('account_id', 'type')
          .annotate(total=Sum('amount'))
    )
    acc_totals = {}
    for row in totals:
        aid = row['account_id']
        typ = row['type']
        acc_totals.setdefault(aid, {'in': Decimal('0'), 'out': Decimal('0')})
        if typ == 'income':
            acc_totals[aid]['in'] += row['total'] or 0
        else:
            acc_totals[aid]['out'] += row['total'] or 0
    for a in accounts:
        opening = Decimal(a.balance or 0)
        in_sum = acc_totals.get(a.id, {}).get('in', Decimal('0'))
        out_sum = acc_totals.get(a.id, {}).get('out', Decimal('0'))
        a.live_balance = opening + in_sum - out_sum

    context = {
        'income': income, 'expense': expense, 'net': net, 'spent':spent,
        'live_total': live_total, 'live_money':live_money,
        'exp_daily_labels': exp_daily_labels, 'exp_daily_values': exp_daily_values,
        'live_after_month_expense': live_after_month_expense, 
        'chart_labels': chart_labels, 'chart_values': chart_values,
        'budgets': budgets, 'spent_map': spent_map,
        'budget_labels': budget_labels, 'budget_values': budget_values, 'spent_values': spent_values,
        'accounts':accounts,
    }
    return render(request, 'dashboard.html', context)

# ---------- Transactions ----------

@login_required
def transaction_list(request):
    tx = Transaction.objects.filter(user=request.user).select_related('account','category')
    q = request.GET.get('q', '').strip()
    account_id = request.GET.get('account')
    if q:
        tx = tx.filter(note__icontains=q) | tx.filter(category__name__icontains=q)
    if account_id:
        try:
            tx = tx.filter(account_id=int(account_id))
        except ValueError:
            pass
    accounts = Account.objects.filter(user=request.user).order_by('name')
    return render(request, 'transactions/list.html', {'tx': tx, 'q': q, 'accounts': accounts, 'account_id': account_id})

@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        form.instance.user = request.user
        if form.is_valid():
            form.save()
            return redirect('transactions')
    else:
        form = TransactionForm()
    form.fields['account'].queryset = Account.objects.filter(user=request.user)
    form.fields['category'].queryset = Category.objects.filter(user=request.user)
    return render(request, 'transactions/form.html', {'form': form, 'title': 'Add Transaction'})

@login_required
def transaction_update(request, pk):
    obj = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('transactions')
    else:
        form = TransactionForm(instance=obj)
    form.fields['account'].queryset = Account.objects.filter(user=request.user)
    form.fields['category'].queryset = Category.objects.filter(user=request.user)
    return render(request, 'transactions/form.html', {'form': form, 'title': 'Edit Transaction'})

@login_required
def transaction_delete(request, pk):
    obj = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        return redirect('transactions')
    return render(request, 'transactions/confirm_delete.html', {'obj': obj})

# ---------- Categories ----------

@login_required
def category_list(request):
    cats = Category.objects.filter(user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, user=request.user)
        form.instance.user = request.user
        if form.is_valid():
            form.save(); return redirect('categories')
    else:
        form = CategoryForm(user=request.user)
    return render(request, 'budgets/list.html', {'cats': cats, 'form': form, 'type': 'category'})

@login_required
def category_create(request):
    return redirect('categories')

@login_required
def category_update(request, pk):
    obj = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('categories')
    else:
        form = CategoryForm(instance=obj, user=request.user)
    return render(request, 'categories/form.html', {'form': form, 'title': 'Edit Category'})

@login_required
def category_delete(request, pk):
    obj = get_object_or_404(Category, pk=pk, user=request.user)
    error = None
    if request.method == 'POST':
        try:
            obj.delete()
            return redirect('categories')
        except ProtectedError:
            error = "You can't delete this category because it is used by one or more transactions."
    return render(request, 'categories/confirm_delete.html', {'obj': obj, 'error': error})

# ---------- Accounts ----------

@login_required
def account_list(request):
    accounts = Account.objects.filter(user=request.user).order_by('name')

    # Compute live balances: opening + income - expense per account
    tx = Transaction.objects.filter(user=request.user)
    totals = (
        tx.values('account_id', 'type')
          .annotate(total=Sum('amount'))
    )
    acc_totals = {}
    for row in totals:
        aid = row['account_id']
        typ = row['type']
        acc_totals.setdefault(aid, {'in': Decimal('0'), 'out': Decimal('0')})
        if typ == 'income':
            acc_totals[aid]['in'] += row['total'] or 0
        else:
            acc_totals[aid]['out'] += row['total'] or 0
    for a in accounts:
        opening = Decimal(a.balance or 0)
        in_sum = acc_totals.get(a.id, {}).get('in', Decimal('0'))
        out_sum = acc_totals.get(a.id, {}).get('out', Decimal('0'))
        a.live_balance = opening + in_sum - out_sum

    if request.method == 'POST':
        form = AccountForm(request.POST, user=request.user)
        form.instance.user = request.user
        if form.is_valid():
            form.save(); return redirect('accounts')
    else:
        form = AccountForm(user=request.user)

    return render(request, 'budgets/list.html', {
        'accounts': accounts,
        'form': form,
        'type': 'account',
    })

@login_required
def account_create(request):
    return redirect('accounts')

@login_required
def account_update(request, pk):
    obj = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=obj, user=request.user)
        if form.is_valid():
            form.save(); return redirect('accounts')
    else:
        form = AccountForm(instance=obj, user=request.user)
    return render(request, 'accounts/form.html', {'form': form, 'title': 'Edit Account'})

@login_required
def account_delete(request, pk):
    obj = get_object_or_404(Account, pk=pk, user=request.user)
    error = None
    if request.method == 'POST':
        try:
            obj.delete(); return redirect('accounts')
        except ProtectedError:
            error = "You can't delete this account because it is used by one or more transactions."
    return render(request, 'accounts/confirm_delete.html', {'obj': obj, 'error': error})

@login_required
def account_transfer(request):
    # Create paired expense/income transactions
    if request.method == 'POST':
        form = TransferForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            src = form.cleaned_data['from_account']
            dst = form.cleaned_data['to_account']
            amt = form.cleaned_data['amount']
            dt  = form.cleaned_data['date']
            note = form.cleaned_data['note'] or ''

            # Ensure transfer categories exist
            cat_out, _ = Category.objects.get_or_create(user=user, name='Transfer', type='expense')
            cat_in,  _ = Category.objects.get_or_create(user=user, name='Transfer', type='income')

            # Outflow from source
            Transaction.objects.create(
                user=user, account=src, category=cat_out, type='expense', amount=amt,
                date=dt, note=f'Transfer to {dst.name}. {note}'.strip()
            )
            # Inflow to destination
            Transaction.objects.create(
                user=user, account=dst, category=cat_in, type='income', amount=amt,
                date=dt, note=f'Transfer from {src.name}. {note}'.strip()
            )
            messages.success(request, 'Transfer recorded.')
            return redirect('transactions')
    else:
        form = TransferForm(user=request.user)
    return render(request, 'accounts/transfer.html', {'form': form, 'title': 'Transfer Between Accounts'})

# ---------- Budgets ----------

@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user).select_related('category')
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        form.fields['category'].queryset = Category.objects.filter(user=request.user)
        form.instance.user = request.user
        if form.is_valid():
            form.save(); return redirect('budgets')
    else:
        form = BudgetForm()
    return render(request, 'budgets/list.html', {'budgets': budgets, 'form': form, 'type': 'budget'})

@login_required
def budget_create(request):
    return redirect('budgets')

@login_required
def budget_update(request, pk):
    obj = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=obj)
        form.fields['category'].queryset = Category.objects.filter(user=request.user)
        if form.is_valid():
            form.save()
            return redirect('budgets')
    else:
        form = BudgetForm(instance=obj)
        form.fields['category'].queryset = Category.objects.filter(user=request.user)
    return render(request, 'budgets/form.html', {'form': form, 'title': 'Edit Budget'})

@login_required
def budget_delete(request, pk):
    obj = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        return redirect('budgets')
    return render(request, 'budgets/confirm_delete.html', {'obj': obj})