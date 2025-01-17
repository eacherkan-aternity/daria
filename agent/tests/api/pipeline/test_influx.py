from agent import pipeline


class TestInflux:
    params = {
        'test_source_create': [{
            'data': [{
                'type': 'influx',
                'name': 'influx',
                'config': {
                    'host': 'http://influx:8086',
                    'username': 'admin',
                    'password': 'admin',
                    'db': 'test',
                }
            }],
            'er': [{"config": {"db": "test", "host": "http://influx:8086", "password": "admin", "username": "admin"},
                    "name": "influx", "type": "influx"}]
        }],
        'test_create': [{
            'data': [{
                "source": "influx",
                "pipeline_id": "test_influx",
                "measurement_name": "wrong",
                "values": {"wrong": "gauge"},
                "dimensions": {
                    "required": [],
                    "optional": ["wrong"]
                },
                "properties": {"test": "wrong"},
                "interval": 5,
                "uses_schema": False
            }],
            'er': [{
                "dimensions": {"optional": ["wrong"], "required": []}, "interval": 5,
                "measurement_name": "wrong", "override_source": {}, "pipeline_id": "test_influx",
                "properties": {"test": "wrong"}, "source": "influx",
                "values": {"wrong": "gauge"}, "uses_schema": False, 'timestamp': {'name': 'time', 'type': 'unix_ms'},
            }]
        }],
        'test_edit': [{
            'data': [{
                "source": "influx",
                "pipeline_id": "test_influx",
                "measurement_name": "cpu_test",
                "values": {"usage_active": "gauge"},
                "dimensions": {
                    "required": [],
                    "optional": ["cpu", "host", "zone"]
                },
                "properties": {"test": "val"},
                "interval": 5
            }],
            'er': [{
                "dimensions": {"optional": ["cpu", "host", "zone"], "required": []}, "interval": 5,
                "measurement_name": "cpu_test", "override_source": {}, "pipeline_id": "test_influx",
                "properties": {"test": "val"}, "source": "influx",
                "values": {"usage_active": "gauge"}, "uses_schema": False, 'timestamp': {'name': 'time', 'type': 'unix_ms'}}]
        }],
    }

    def test_source_create(self, api_client, data, er):
        result = api_client.post('/sources', json=list(data))
        assert result.json == er

    def test_create(self, api_client, data, er):
        result = api_client.post('/pipelines', json=list(data))
        assert result.json == er

    def test_edit(self, api_client, data, er):
        result = api_client.put('/pipelines', json=list(data))
        assert result.json == er

    def test_start(self, api_client):
        result = api_client.post('/pipelines/test_influx/start')
        assert result.status_code == 200

    def test_info(self, api_client):
        result = api_client.get('/pipelines/test_influx/info')
        assert result.status_code == 200
        assert len(result.data) != 0

    def test_logs(self, api_client):
        result = api_client.get('/pipelines/test_influx/logs')
        assert result.status_code == 200
        assert len(result.data) != 0

    def test_enable_destination_logs(self, api_client):
        result = api_client.post('/pipelines/test_influx/force-stop')
        assert result.status_code == 200
        result = api_client.post('/pipelines/test_influx/enable-destination-logs')
        assert result.status_code == 200

    def test_disable_destination_logs(self, api_client):
        result = api_client.post('/pipelines/test_influx/disable-destination-logs')
        assert result.status_code == 200

    def test_reset(self, api_client):
        result = api_client.post('/pipelines/test_influx/reset')
        assert result.status_code == 200

    def test_pipeline_failed(self, api_client):
        pipeline_id = 'test_influx'
        pipeline_status = 'RUN_ERROR'
        res = api_client.post(f'/pipeline-status-change/{pipeline_id}', json={
            "pipeline_status": pipeline_status,
            "time": "1970-01-01 00:00:00"
        })
        assert res.status_code == 200
        assert pipeline.repository.get_by_id(pipeline_id).status == pipeline_status

    def test_delete(self, api_client):
        pipeline_id = 'test_influx'
        api_client.delete(f'/pipelines/{pipeline_id}')
        result = api_client.get('/pipelines')
        for obj in result.json:
            if obj['pipeline_id'] == pipeline_id:
                raise Exception

    def test_source_delete(self, api_client):
        source = 'influx'
        api_client.delete(f'/sources/{source}')
        result = api_client.get('/sources')
        assert source not in result.json
