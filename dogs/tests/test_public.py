from dogs.models import Dog


def test_public_list_renders(client):
    Dog.objects.create(name='Buddy')
    response = client.get('/dogs/')

    assert response.status_code == 200
    assert b'Dog Pound' in response.content


def test_public_list_filters_pound_dogs(client):
    Dog.objects.create(name='Impounded', status=Dog.Status.IMPOUNDED)
    Dog.objects.create(name='Available', status=Dog.Status.AVAILABLE)
    Dog.objects.create(name='Adopted', status=Dog.Status.ADOPTED)
    Dog.objects.create(name='Reclaimed', status=Dog.Status.RECLAIMED)
    Dog.objects.create(name='Released', status=Dog.Status.RELEASED)

    response = client.get('/dogs/')

    assert response.status_code == 200
    dogs = list(response.context['dogs'])
    assert {dog.name for dog in dogs} == {'Impounded', 'Available'}


def test_public_detail_404(client):
    response = client.get('/dogs/9999/')

    assert response.status_code == 404
