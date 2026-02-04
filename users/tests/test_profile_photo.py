from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from users.models import CustomUser


def make_image_file(name='avatar.jpg', size=(120, 120), color=(20, 120, 110)):
    buffer = BytesIO()
    image = Image.new('RGB', size, color=color)
    image.save(buffer, format='JPEG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/jpeg')


def create_user():
    return CustomUser.objects.create_user(
        username='profileuser',
        email='profile@example.com',
        password='StrongPass123!',
        legal_consent=True,
    )


def test_profile_photo_upload_success(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user = create_user()
    client.force_login(user)

    image_file = make_image_file()
    response = client.post(reverse('profile'), {'profile_photo': image_file})

    assert response.status_code == 302
    user.profile.refresh_from_db()
    assert user.profile.profile_photo.name
    assert user.profile.profile_photo.storage.exists(user.profile.profile_photo.name)


def test_profile_photo_optional_keeps_existing(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user = create_user()
    client.force_login(user)

    initial_file = make_image_file(name='initial.jpg')
    user.profile.profile_photo.save('initial.jpg', initial_file, save=True)
    original_name = user.profile.profile_photo.name

    response = client.post(reverse('profile'), {'full_name': 'Updated Name'}, follow=True)

    assert response.status_code == 200
    user.profile.refresh_from_db()
    assert user.profile.profile_photo.name == original_name


def test_profile_photo_rejects_non_image(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user = create_user()
    client.force_login(user)

    bad_file = SimpleUploadedFile('not-image.txt', b'not an image', content_type='text/plain')
    response = client.post(reverse('profile'), {'profile_photo': bad_file})

    assert response.status_code == 200
    assert 'profile_photo' in response.context['form'].errors
    user.profile.refresh_from_db()
    assert not user.profile.profile_photo
