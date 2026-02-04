(() => {
  const form = document.getElementById('reportForm');
  if (!form) return;

  const reportType = document.getElementById('reportType');
  const description = document.getElementById('description');
  const alertBox = document.getElementById('reportAlert');
  const submitBtn = document.getElementById('submitBtn');

  const latInput = document.getElementById('latInput');
  const lngInput = document.getElementById('lngInput');
  const mapsUrl = document.getElementById('mapsUrl');
  const geoBtn = document.getElementById('geoBtn');
  const dogMedia = document.getElementById('dogMedia');

  const fullName = document.getElementById('fullName');
  const phone = document.getElementById('phone');
  const street = document.getElementById('street');
  const barangay = document.getElementById('barangay');
  const city = document.getElementById('city');
  const province = document.getElementById('province');
  const postalCode = document.getElementById('postalCode');


  const showAlert = (type, messages) => {
    if (!alertBox) return;
    alertBox.classList.remove('d-none', 'alert-success', 'alert-danger');
    alertBox.classList.add(`alert-${type}`);
    if (Array.isArray(messages)) {
      alertBox.innerHTML = messages.join('<br>');
    } else {
      alertBox.textContent = messages;
    }
  };

  const clearAlert = () => {
    if (!alertBox) return;
    alertBox.classList.add('d-none');
    alertBox.textContent = '';
  };

  const updateMapsUrl = () => {
    const lat = parseFloat(latInput.value);
    const lng = parseFloat(lngInput.value);
    if (!Number.isNaN(lat) && !Number.isNaN(lng)) {
      mapsUrl.value = `https://maps.google.com/?q=${lat},${lng}`;
    }
  };

  const parseLatLngFromUrl = (value) => {
    if (!value) return null;
    const patterns = [
      /@(-?\d+\.?\d*),(-?\d+\.?\d*)/,
      /q=(-?\d+\.?\d*),(-?\d+\.?\d*)/,
      /ll=(-?\d+\.?\d*),(-?\d+\.?\d*)/,
    ];
    for (const pattern of patterns) {
      const match = value.match(pattern);
      if (match) {
        return { lat: match[1], lng: match[2] };
      }
    }
    return null;
  };

  if (latInput && lngInput) {
    latInput.addEventListener('input', updateMapsUrl);
    lngInput.addEventListener('input', updateMapsUrl);
  }

  if (mapsUrl) {
    mapsUrl.addEventListener('input', () => {
      const parsed = parseLatLngFromUrl(mapsUrl.value);
      if (parsed) {
        latInput.value = parsed.lat;
        lngInput.value = parsed.lng;
      }
    });
  }

  if (geoBtn) {
    if (!navigator.geolocation) {
      geoBtn.disabled = true;
      geoBtn.textContent = 'Geolocation not supported';
    } else {
      geoBtn.addEventListener('click', () => {
        geoBtn.disabled = true;
        geoBtn.textContent = 'Locating...';
        navigator.geolocation.getCurrentPosition(
          (position) => {
            latInput.value = position.coords.latitude.toFixed(6);
            lngInput.value = position.coords.longitude.toFixed(6);
            updateMapsUrl();
            geoBtn.disabled = false;
            geoBtn.textContent = 'Use my current location';
          },
          () => {
            showAlert('danger', 'Unable to access your location.');
            geoBtn.disabled = false;
            geoBtn.textContent = 'Use my current location';
          }
        );
      });
    }
  }

  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  };

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearAlert();

    const errors = [];
    const reportTypeValue = reportType.value.trim();
    if (!reportTypeValue) {
      errors.push('Report type is required.');
    }

    const descriptionValue = description.value.trim();
    if (!descriptionValue) {
      errors.push('Description is required.');
    }

    let location = { lat: null, lng: null, maps_url: null, address: null };
    let contactName = '';
    let contactPhone = '';

    const latValue = parseFloat(latInput.value);
    const lngValue = parseFloat(lngInput.value);
    if (Number.isNaN(latValue) || Number.isNaN(lngValue)) {
      errors.push('Latitude and longitude are required for Google Maps.');
    } else {
      location.lat = latValue;
      location.lng = lngValue;
      location.maps_url = mapsUrl.value.trim() || `https://maps.google.com/?q=${latValue},${lngValue}`;
    }
    if (!mapsUrl.value.trim()) {
      errors.push('Google Maps URL is required.');
    }

    contactName = fullName.value.trim();
    contactPhone = phone.value.trim();
    if (!contactName) {
      errors.push('Full name is required for manual address.');
    }

    const address = {
      street: street.value.trim(),
      barangay: barangay.value.trim(),
      city: city.value.trim(),
      province: province.value.trim(),
      postal_code: postalCode.value.trim(),
    };

    const requiredFields = ['street', 'city', 'province', 'postal_code'];
    requiredFields.forEach((field) => {
      if (!address[field]) {
        errors.push(`${field.replace('_', ' ')} is required.`);
      }
    });

    location.address = address;

    if (errors.length) {
      showAlert('danger', errors);
      return;
    }

    const payload = {
      report_type: reportTypeValue,
      description: descriptionValue,
      location_method: 'both',
      location,
      created_at: new Date().toISOString(),
      contact_name: contactName,
      contact_phone: contactPhone,
    };

    try {
      submitBtn.disabled = true;
      const formData = new FormData();
      formData.append('payload', JSON.stringify(payload));
      if (dogMedia && dogMedia.files && dogMedia.files[0]) {
        formData.append('photo', dogMedia.files[0]);
      }
      const response = await fetch('/api/reports', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        if (data && data.errors) {
          const apiErrors = Object.values(data.errors).map((value) => value);
          showAlert('danger', apiErrors);
        } else {
          showAlert('danger', 'Unable to submit your report. Please try again.');
        }
        return;
      }

      showAlert('success', `Report submitted successfully. Your report ID is ${data.report_id}.`);
      form.reset();
    } catch (error) {
      showAlert('danger', 'Something went wrong. Please try again later.');
    } finally {
      submitBtn.disabled = false;
    }
  });
})();
