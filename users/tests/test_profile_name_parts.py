from django.urls import reverse

from users.models import CustomUser


def create_user():
    return CustomUser.objects.create_user(
        username='namepartsuser',
        email='nameparts@example.com',
        password='StrongPass123!',
        legal_consent=True,
    )


def test_profile_name_parts_build_full_name(client):
    user = create_user()
    client.force_login(user)

    response = client.post(
        reverse('profile'),
        {
            'first_name': 'Juan',
            'middle_name': 'Santos',
            'last_name': 'Dela Cruz',
            'gender': 'MALE',
            'address': 'Bayawan City',
        },
    )

    assert response.status_code == 302
    user.profile.refresh_from_db()
    assert user.profile.full_name == 'Juan Santos Dela Cruz'


def test_profile_name_parts_preserve_full_name_when_no_parts_sent(client):
    user = create_user()
    user.profile.full_name = 'Existing Name'
    user.profile.save(update_fields=['full_name'])
    client.force_login(user)

    response = client.post(reverse('profile'), {'address': 'Updated Address'})

    assert response.status_code == 302
    user.profile.refresh_from_db()
    assert user.profile.full_name == 'Existing Name'
