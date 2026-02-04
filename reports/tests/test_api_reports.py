import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from reports.models import Report


def test_api_reports_google_maps_and_address_success(client):
    payload = {
        'report_type': 'incident',
        'description': 'Loose dog near the market.',
        'location_method': 'both',
        'location': {
            'lat': 9.3639,
            'lng': 122.8072,
            'maps_url': 'https://maps.google.com/?q=9.3639,122.8072',
            'address': {
                'street': 'Rizal St.',
                'barangay': 'Poblacion',
                'city': 'Bayawan',
                'province': 'Negros Oriental',
                'postal_code': '6221',
            },
        },
        'created_at': '2026-02-03T00:00:00Z',
        'contact_name': 'Juan Dela Cruz',
    }

    response = client.post(
        reverse('api_reports'),
        data=json.dumps(payload),
        content_type='application/json',
    )

    assert response.status_code == 201
    data = response.json()
    report = Report.objects.get(id=data['report_id'])
    assert report.location_method == Report.LocationMethod.BOTH
    assert float(report.latitude) == payload['location']['lat']
    assert float(report.longitude) == payload['location']['lng']


def test_api_reports_accepts_photo_upload(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    payload = {
        'report_type': 'incident',
        'description': 'Dog spotted with a collar.',
        'location_method': 'both',
        'location': {
            'lat': 9.3639,
            'lng': 122.8072,
            'maps_url': 'https://maps.google.com/?q=9.3639,122.8072',
            'address': {
                'street': 'Rizal St.',
                'barangay': 'Poblacion',
                'city': 'Bayawan',
                'province': 'Negros Oriental',
                'postal_code': '6221',
            },
        },
        'created_at': '2026-02-03T00:00:00Z',
        'contact_name': 'Juan Dela Cruz',
    }
    photo = SimpleUploadedFile('dog.jpg', b'fake-image-bytes', content_type='image/jpeg')

    response = client.post(
        reverse('api_reports'),
        data={'payload': json.dumps(payload), 'photo': photo},
    )

    assert response.status_code == 201
    data = response.json()
    report = Report.objects.get(id=data['report_id'])
    assert report.photo.name


def test_api_reports_accepts_video_upload(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    payload = {
        'report_type': 'incident',
        'description': 'Video evidence submitted.',
        'location_method': 'both',
        'location': {
            'lat': 9.3639,
            'lng': 122.8072,
            'maps_url': 'https://maps.google.com/?q=9.3639,122.8072',
            'address': {
                'street': 'Rizal St.',
                'barangay': 'Poblacion',
                'city': 'Bayawan',
                'province': 'Negros Oriental',
                'postal_code': '6221',
            },
        },
        'created_at': '2026-02-03T00:00:00Z',
        'contact_name': 'Juan Dela Cruz',
    }
    video = SimpleUploadedFile('dog.mp4', b'fake-video-bytes', content_type='video/mp4')

    response = client.post(
        reverse('api_reports'),
        data={'payload': json.dumps(payload), 'photo': video},
    )

    assert response.status_code == 201
    data = response.json()
    report = Report.objects.get(id=data['report_id'])
    assert report.photo.name.endswith('.mp4')


def test_api_reports_missing_fields_failure(client):
    payload = {
        'report_type': 'incident',
        'description': 'Missing location details.',
        'location_method': 'both',
        'location': {'lat': None, 'lng': None},
        'created_at': '2026-02-03T00:00:00Z',
    }

    response = client.post(
        reverse('api_reports'),
        data=json.dumps(payload),
        content_type='application/json',
    )

    assert response.status_code == 400
    data = response.json()
    assert 'google_maps' in data['errors']


def test_api_reports_missing_address_failure(client):
    payload = {
        'report_type': 'incident',
        'description': 'Missing address fields.',
        'location_method': 'both',
        'location': {
            'lat': 9.3639,
            'lng': 122.8072,
            'maps_url': 'https://maps.google.com/?q=9.3639,122.8072',
            'address': {
                'street': '',
                'barangay': '',
                'city': '',
                'province': '',
                'postal_code': '',
            },
        },
        'created_at': '2026-02-03T00:00:00Z',
        'contact_name': 'Juan Dela Cruz',
    }

    response = client.post(
        reverse('api_reports'),
        data=json.dumps(payload),
        content_type='application/json',
    )

    assert response.status_code == 400
    data = response.json()
    assert 'street' in data['errors']
