from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db.models import Sum, Avg
from django.http import JsonResponse
from django.utils.timezone import now
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from crypto.models import Crypto
from strategy.models import UsersInStrategy
from transaction.models import TransactionOpen, TransactionClose
from transaction.serializers import TransactionSerializer
from .models import Trader, TraderProfitHistory, TrendingThreshold
from .permissions import IsSuperUserOrReadOnly, IsSuperUser
from .serializers import TraderSerializer, TrendingThresholdSerializer


class TraderViewSet(ModelViewSet):
    queryset = Trader.objects.all()
    serializer_class = TraderSerializer
    permission_classes = (IsSuperUserOrReadOnly,)

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(visible=True)

        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        users = UsersInStrategy.objects.filter(strategy__trader=instance).exists()
        if users:
            return JsonResponse({'error': 'You cannot delete this trader because it has users.'})
        self.perform_destroy(instance)
        return Response(status=204)

    @action(detail=False, methods=['get'])
    def my(self, request, *args, **kwargs):
        my_traders = UsersInStrategy.objects.filter(user=request.user).values_list('strategy__trader',
                                                                                   flat=True).distinct()
        return JsonResponse({'my_traders_copied_id': list(my_traders)}, safe=False)

    @extend_schema(
        responses=TransactionSerializer(many=True),
    )
    @action(detail=True, methods=['get'])
    def transactions(self, request, *args, **kwargs):
        trader = self.get_object()
        transactions = trader.transaction_set.all().order_by('-close_time')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def get_stats(self, request, *args, **kwargs):
        trader = self.get_object()

        result = Crypto.objects.filter(strategy__trader=trader).values('name').annotate(total=Sum('total_value'))
        result_dict = {item['name']: item['total'] for item in result}

        summary = sum(result_dict.values())

        for key, value in result_dict.items():
            result_dict[key] = round(value / summary * 100, 2)

        response = trader.get_stats()
        response['get_cryptos_in_percentage'] = result_dict

        return JsonResponse(response, safe=False)

    @action(detail=True, methods=['get'])
    def get_open_transactions(self, request, *args, **kwargs):
        trader = self.get_object()

        transactions = TransactionOpen.objects.filter(strategy__trader=trader).order_by('-open_time')
        serializer = TransactionSerializer(transactions, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def get_close_transactions(self, request, *args, **kwargs):
        trader = self.get_object()

        transactions = TransactionClose.objects.filter(strategy__trader=trader).order_by('-close_time')
        serializer = TransactionSerializer(transactions, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def get_all_trending_traders(self, request, *args, **kwargs):
        traders = Trader.objects.filter(trader_type='trending', visible=True)
        serializer = TraderSerializer(traders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def get_profit_chart(self, request, *args, **kwargs):
        trader = self.get_object()
        end_date = now()
        periods = {
            '7days': end_date - relativedelta(days=7),
            '1month': end_date - relativedelta(months=1),
            '3months': end_date - relativedelta(months=3),
            'all_time': None
        }

        chart_info = {}

        for period, start_date in periods.items():
            if start_date:
                profits = TraderProfitHistory.objects.filter(trader=trader, date__range=[start_date, end_date])
            else:
                profits = TraderProfitHistory.objects.filter(trader=trader)

            interval_count = 7

            total_days = (end_date - (start_date if start_date else profits.earliest('date').date)).days
            days_per_interval = total_days // interval_count

            if period == 'all_time' and days_per_interval < 4:
                days_per_interval = 4
                start_date = end_date - relativedelta(months=1)

            interval_data = []
            for i in range(interval_count):
                interval_start = start_date + timedelta(days=i * days_per_interval) if start_date else profits.earliest(
                    'date').date + timedelta(days=i * days_per_interval)
                interval_end = interval_start + timedelta(days=days_per_interval)

                avg_profit = profits.filter(date__range=[interval_start, interval_end]).aggregate(Avg('value'))[
                                 'value__avg'] or 0

                interval_data.append({
                    'date': end_date if i == 6 else interval_end,
                    'average_profit': avg_profit
                })

            chart_info[period] = interval_data

        return JsonResponse(chart_info, safe=False)

    @action(detail=True, methods=['get'])
    def get_traders_profit_chart(self, request, *args, **kwargs):

        trader = self.get_object()
        end_date = now()
        periods = {
            '7days': end_date - timedelta(days=7),
            '1month': end_date - timedelta(days=30),
            '3months': end_date - timedelta(days=90),
            'all_time': None
        }

        chart_info = {}

        for period, start_date in periods.items():
            if start_date:
                traders_profit = TraderProfitHistory.objects.filter(date__range=[start_date, end_date])
                profits = traders_profit.filter(trader=trader)
            else:
                traders_profit = TraderProfitHistory.objects.all()
                profits = traders_profit.filter(trader=trader)

            interval_count = 7

            total_days = (end_date - (start_date if start_date else profits.earliest('date').date)).days
            days_per_interval = total_days // interval_count

            if period == 'all_time' and days_per_interval < 4:
                days_per_interval = 4
                start_date = end_date - relativedelta(months=1)

            interval_data = []
            for i in range(interval_count):
                interval_start = start_date + timedelta(days=i * days_per_interval) if start_date else profits.earliest(
                    'date').date + timedelta(days=i * days_per_interval)
                interval_end = interval_start + timedelta(days=days_per_interval)

                avg_profit = profits.filter(date__range=[interval_start, interval_end]).aggregate(Avg('value'))[
                                 'value__avg'] or 0

                traders_avg_profit = \
                    traders_profit.filter(date__range=[interval_start, interval_end]).aggregate(Avg('value'))[
                        'value__avg'] or 0

                interval_data.append({
                    'date': end_date if i == 6 else interval_end,
                    'average_profit': avg_profit,
                    'traders_profit': traders_avg_profit
                })

            chart_info[period] = interval_data

        return JsonResponse(chart_info, safe=False)


class TrendingThresholdView(APIView):
    permission_classes = (IsSuperUser, )

    def get(self, request):
        threshold = TrendingThreshold.objects.first()
        serializer = TrendingThresholdSerializer(threshold)
        return Response(serializer.data)

    def post(self, request):
        serializer = TrendingThresholdSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.data

            threshold = TrendingThreshold.objects.first()
            if threshold is None:
                TrendingThreshold.objects.create(**data)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            threshold.min_copiers = data['min_copiers']
            threshold.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
