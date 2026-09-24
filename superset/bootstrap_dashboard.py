"""Create Featured Charts on Superset 5.0.0; safe to run repeatedly."""
import json
import os
from superset.app import create_app
from superset import db, security_manager


def main():
    with create_app().app_context():
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice
        from superset.connectors.sqla.models import SqlaTable, SqlMetric
        owner = security_manager.find_user(username=os.environ.get('SUPERSET_ADMIN_USERNAME', 'admin'))
        database = db.session.query(Database).filter_by(database_name='Northwind Lakehouse').one_or_none()
        if database is None:
            database = Database(database_name='Northwind Lakehouse')
            database.set_sqlalchemy_uri('trino://superset@lakehouse-trino:8080/iceberg/northwind_gold')
            database.allow_dml = False
            db.session.add(database)
            db.session.flush()
        dataset = db.session.query(SqlaTable).filter_by(database_id=database.id, schema='northwind_gold',
                                                       table_name='sales_dashboard').one_or_none()
        if dataset is None:
            dataset = SqlaTable(database=database, schema='northwind_gold', table_name='sales_dashboard',
                                main_dttm_col='order_date', owners=[owner])
            db.session.add(dataset)
            db.session.flush()
        dataset.fetch_metadata()
        metrics = {'revenue': 'SUM(net_revenue)', 'orders': 'COUNT(DISTINCT order_id)', 'units': 'SUM(quantity)'}
        for name, expression in metrics.items():
            if not any(m.metric_name == name for m in dataset.metrics):
                dataset.metrics.append(SqlMetric(metric_name=name, expression=expression))
        dashboard = db.session.query(Dashboard).filter_by(slug='featured-charts').one_or_none()
        if dashboard is None:
            dashboard = Dashboard(dashboard_title='Featured Charts', slug='featured-charts', owners=[owner])
            db.session.add(dashboard)
        dashboard.changed_by_fk = owner.id
        dashboard.published = True
        specs = [
            ('Net Revenue (THB)', 'big_number_total', 'revenue', [], {}),
            ('Orders with Sales', 'big_number_total', 'orders', [], {}),
            ('Units Sold', 'big_number_total', 'units', [], {}),
            ('Daily Revenue', 'echarts_timeseries_line', 'revenue', [], {'is_timeseries': True}),
            ('Revenue by Shipper', 'pie', 'revenue', ['shipper_name'], {}),
            ('Top 10 Products', 'table', 'revenue', ['product_name'], {'row_limit': 10}),
        ]
        charts = []
        for title, viz, metric, columns, options in specs:
            chart = db.session.query(Slice).filter_by(slice_name=title, datasource_id=dataset.id,
                                                       datasource_type='table').one_or_none()
            if chart is None:
                chart = Slice(slice_name=title, datasource_id=dataset.id, datasource_type='table', owners=[owner])
                db.session.add(chart)
            chart.viz_type = viz
            params = dict(viz_type=viz, datasource=f'{dataset.id}__table', metric=metric, metrics=[metric],
                          groupby=columns, columns=columns, adhoc_filters=[], time_range='No filter',
                          granularity_sqla='order_date', time_grain_sqla='P1D', row_limit=options.get('row_limit', 10000),
                          color_scheme='supersetColors', number_format=',.2f', y_axis_format=',.0f',
                          show_legend=True, show_labels=True, donut=True, query_mode='aggregate',
                          order_desc=True, x_axis='order_date', seriesType='line')
            if viz == 'big_number_total':
                params.update(subheader='Northwind Thailand', y_axis_format=',.2f' if metric == 'revenue' else ',.0f')
            chart.params = json.dumps(params)
            query = dict(columns=columns, metrics=[metric], filters=[], time_range='No filter',
                         granularity='order_date', is_timeseries=options.get('is_timeseries', False),
                         extras={'time_grain_sqla': 'P1D', 'having': '', 'where': ''},
                         row_limit=options.get('row_limit', 10000), orderby=[[metric, False]])
            chart.query_context = json.dumps(dict(datasource={'id': dataset.id, 'type': 'table'},
                                                   queries=[query], form_data=params,
                                                   result_format='json', result_type='full'))
            charts.append(chart)
        db.session.flush()
        position = {
            'DASHBOARD_VERSION_KEY': 'v2',
            'ROOT_ID': {'id': 'ROOT_ID', 'type': 'ROOT', 'children': ['GRID_ID']},
            'GRID_ID': {'id': 'GRID_ID', 'type': 'GRID', 'children': ['ROW-kpis', 'ROW-analysis']},
            'HEADER_ID': {'id': 'HEADER_ID', 'type': 'HEADER', 'meta': {'text': 'Featured Charts'}},
        }
        for row_index, row_id in enumerate(['ROW-kpis', 'ROW-analysis']):
            row_charts = charts[row_index*3:(row_index+1)*3]
            position[row_id] = dict(id=row_id, type='ROW', parents=['ROOT_ID', 'GRID_ID'],
                                    children=[f'CHART-{c.id}' for c in row_charts], meta={'background': 'BACKGROUND_TRANSPARENT'})
            for chart in row_charts:
                key = f'CHART-{chart.id}'
                position[key] = dict(id=key, type='CHART', parents=['ROOT_ID', 'GRID_ID', row_id], children=[],
                                      meta=dict(chartId=chart.id, width=4, height=22 if row_index == 0 else 52,
                                                sliceName=chart.slice_name))
        dashboard.slices = charts
        dashboard.position_json = json.dumps(position)
        dashboard.json_metadata = json.dumps({'color_scheme': 'supersetColors', 'refresh_frequency': 0})
        db.session.commit()
        print(f'Created /superset/dashboard/featured-charts/ with {len(charts)} charts, dataset={dataset.id}')


if __name__ == '__main__':
    main()
