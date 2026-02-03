from django.urls import reverse


def test_home_page_renders(client):
    response = client.get(reverse('home'))

    assert response.status_code == 200
    assert b"Bayawan" in response.content
