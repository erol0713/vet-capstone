from reports.models import Report


def test_public_list_renders(client):
    Report.objects.create(report_type='STRAY', location='Poblacion')

    response = client.get('/reports/')

    assert response.status_code == 200
    assert b'Community Reports' in response.content
