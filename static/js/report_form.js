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
  const mapAddress = document.getElementById('mapAddress');
  const mapSearch = document.getElementById('mapSearch');
  const mapFallback = document.getElementById('mapFallback');
  const mapContainer = document.getElementById('reportMap');
  const mapPreview = document.getElementById('mapPreview');
  const mapPreviewFrame = document.getElementById('mapPreviewFrame');
  const geoBtn = document.getElementById('geoBtn');
  const dogMedia = document.getElementById('dogMedia');

  const fullName = document.getElementById('fullName');
  const phone = document.getElementById('phone');
  const email = document.getElementById('email');
  const street = document.getElementById('street');
  const barangay = document.getElementById('barangay');
  const city = document.getElementById('city');
  const addressNotes = document.getElementById('addressNotes');

  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const stepHint = document.getElementById('stepHint');
  const stepLabel = document.getElementById('stepLabel');
  const progressContainer = document.querySelector('.report-progress');
  const progressBar = document.querySelector('.report-progress .progress-bar');
  const stepElements = Array.from(document.querySelectorAll('[data-report-step]'));
  const stepIndicators = Array.from(document.querySelectorAll('[data-step-indicator]'));
  const totalSteps = stepElements.length || 1;
  let currentStep = 1;

  const previewType = document.getElementById('previewType');
  const previewContact = document.getElementById('previewContact');
  const previewPhone = document.getElementById('previewPhone');
  const previewEmail = document.getElementById('previewEmail');
  const previewAddress = document.getElementById('previewAddress');
  const previewAddressNotes = document.getElementById('previewAddressNotes');
  const previewDescription = document.getElementById('previewDescription');
  const previewMapWrap = document.getElementById('previewMapWrap');
  const previewMap = document.getElementById('previewMap');
  const previewMedia = document.getElementById('previewMedia');

  const summaryCard = document.getElementById('reportSummary');
  const summaryId = document.getElementById('summaryId');
  const summaryStatus = document.getElementById('summaryStatus');
  const summaryType = document.getElementById('summaryType');
  const summaryContact = document.getElementById('summaryContact');
  const summaryPhone = document.getElementById('summaryPhone');
  const summaryEmail = document.getElementById('summaryEmail');
  const summaryAddress = document.getElementById('summaryAddress');
  const summaryAddressNotes = document.getElementById('summaryAddressNotes');
  const summaryDescription = document.getElementById('summaryDescription');
  const summaryMap = document.getElementById('summaryMap');
  const summaryMedia = document.getElementById('summaryMedia');

  const defaultCenter = { lat: 9.3639, lng: 122.8072 };
  let mapInstance = null;
  let mapMarker = null;
  let mapGeocoder = null;
  let hasUserSelected = false;
  let mapAvailable = false;
  let mediaPreviewUrl = null;

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

  const getSelectedReportTypeLabel = () => {
    if (!reportType || !reportType.options.length) return '';
    const selectedOption = reportType.options[reportType.selectedIndex];
    return selectedOption ? selectedOption.textContent.trim() : '';
  };

  const getAddressSummaryText = () => {
    return [street.value.trim(), barangay.value.trim(), city.value.trim()]
      .filter((part) => part)
      .join(', ');
  };

  const clearMediaPreview = (container) => {
    if (!container) return;
    container.innerHTML = '';
    if (mediaPreviewUrl) {
      URL.revokeObjectURL(mediaPreviewUrl);
      mediaPreviewUrl = null;
    }
  };

  const renderMediaPreview = (container) => {
    if (!container) return;
    clearMediaPreview(container);

    if (!(dogMedia && dogMedia.files && dogMedia.files[0])) {
      return;
    }

    const file = dogMedia.files[0];
    mediaPreviewUrl = URL.createObjectURL(file);

    if (file.type.startsWith('video/')) {
      const video = document.createElement('video');
      video.src = mediaPreviewUrl;
      video.controls = true;
      container.appendChild(video);
      return;
    }

    if (file.type.startsWith('image/')) {
      const img = document.createElement('img');
      img.src = mediaPreviewUrl;
      img.alt = 'Reported dog media';
      container.appendChild(img);
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
        return { lat: Number(match[1]), lng: Number(match[2]) };
      }
    }
    return null;
  };

  const updateMapsUrl = (lat, lng) => {
    if (!mapsUrl) return;
    mapsUrl.value = `https://maps.google.com/?q=${lat},${lng}`;
  };

  const setMapAddress = (text) => {
    if (!mapAddress) return;
    mapAddress.value = text || '';
  };

  const updateLatLngInputs = (lat, lng) => {
    if (latInput) latInput.value = lat.toFixed(6);
    if (lngInput) lngInput.value = lng.toFixed(6);
    updateMapsUrl(lat, lng);
  };

  const showMapPreview = (lat, lng) => {
    if (!mapPreview || !mapPreviewFrame) return;
    mapPreviewFrame.src = `https://maps.google.com/maps?q=${lat},${lng}&output=embed`;
    mapPreview.classList.remove('d-none');
  };

  const hideMapPreview = () => {
    if (!mapPreview || !mapPreviewFrame) return;
    mapPreviewFrame.removeAttribute('src');
    mapPreview.classList.add('d-none');
  };

  const updateMapFromLatLng = (lat, lng, addressText = '', markSelected = true) => {
    if (markSelected) {
      updateLatLngInputs(lat, lng);
    } else {
      if (latInput) latInput.value = '';
      if (lngInput) lngInput.value = '';
      if (mapsUrl) mapsUrl.value = '';
      if (!addressText) setMapAddress('');
    }
    if (addressText) setMapAddress(addressText);
    if (markSelected) hasUserSelected = true;
    if (!mapAvailable && markSelected) {
      showMapPreview(lat, lng);
    }
    if (!markSelected) {
      hideMapPreview();
    }
    if (mapInstance && mapMarker) {
      const position = { lat, lng };
      mapMarker.setPosition(position);
      mapInstance.setCenter(position);
    }
    if (mapGeocoder && mapInstance && !addressText && markSelected) {
      mapGeocoder.geocode({ location: { lat, lng } }, (results, status) => {
        if (status === 'OK' && results && results[0]) {
          setMapAddress(results[0].formatted_address);
        }
      });
    }
    updateDraftPreview();
  };

  const initMap = () => {
    if (!mapContainer || !window.google || !window.google.maps) {
      if (mapFallback) mapFallback.classList.remove('d-none');
      if (mapContainer) mapContainer.classList.add('d-none');
      return false;
    }

    mapInstance = new window.google.maps.Map(mapContainer, {
      center: defaultCenter,
      zoom: 14,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
    });

    mapMarker = new window.google.maps.Marker({
      position: defaultCenter,
      map: mapInstance,
      draggable: true,
    });

    mapGeocoder = new window.google.maps.Geocoder();

    if (mapSearch) {
      const searchBox = new window.google.maps.places.SearchBox(mapSearch);
      mapInstance.addListener('bounds_changed', () => {
        searchBox.setBounds(mapInstance.getBounds());
      });
      searchBox.addListener('places_changed', () => {
        const places = searchBox.getPlaces();
        if (!places || !places.length) return;
        const place = places[0];
        if (!place.geometry || !place.geometry.location) return;
        const location = place.geometry.location;
        updateMapFromLatLng(location.lat(), location.lng(), place.formatted_address || '');
        if (place.geometry.viewport) {
          mapInstance.fitBounds(place.geometry.viewport);
        } else {
          mapInstance.setZoom(16);
          mapInstance.setCenter(location);
        }
      });
    }

    mapInstance.addListener('click', (event) => {
      if (!event || !event.latLng) return;
      updateMapFromLatLng(event.latLng.lat(), event.latLng.lng());
    });

    mapMarker.addListener('dragend', (event) => {
      if (!event || !event.latLng) return;
      updateMapFromLatLng(event.latLng.lat(), event.latLng.lng());
    });

    updateMapFromLatLng(defaultCenter.lat, defaultCenter.lng, '', false);
    return true;
  };

  const refreshMap = () => {
    if (!mapInstance || !window.google || !window.google.maps) return;
    window.google.maps.event.trigger(mapInstance, 'resize');
    if (mapMarker) {
      mapInstance.setCenter(mapMarker.getPosition());
    }
  };

  const updateDraftPreview = () => {
    const typeLabel = getSelectedReportTypeLabel() || '-';
    const contactName = fullName.value.trim() || '-';
    const phoneText = phone.value.trim();
    const emailText = email.value.trim();
    const addressText = getAddressSummaryText();
    const addressNotesText = addressNotes.value.trim();
    const descriptionText = description.value.trim() || '-';

    if (previewType) previewType.textContent = typeLabel;
    if (previewContact) previewContact.textContent = contactName;
    if (previewPhone) previewPhone.textContent = phoneText;
    if (previewEmail) previewEmail.textContent = emailText;
    if (previewAddress) previewAddress.textContent = addressText || '-';
    if (previewAddressNotes) previewAddressNotes.textContent = addressNotesText;
    if (previewDescription) previewDescription.textContent = descriptionText;

    const latValue = parseFloat(latInput.value);
    const lngValue = parseFloat(lngInput.value);
    if (previewMap && previewMapWrap && !Number.isNaN(latValue) && !Number.isNaN(lngValue)) {
      previewMap.src = `https://maps.google.com/maps?q=${latValue},${lngValue}&output=embed`;
      previewMapWrap.classList.remove('d-none');
    } else if (previewMap && previewMapWrap) {
      previewMap.removeAttribute('src');
      previewMapWrap.classList.add('d-none');
    }

    renderMediaPreview(previewMedia);
  };

  const getStepLabel = (step) => {
    const stepEl = stepElements.find((item) => Number(item.dataset.reportStep) === step);
    return stepEl ? stepEl.dataset.stepLabel || '' : '';
  };

  const updateNextLabel = () => {
    if (!nextBtn) return;
    nextBtn.textContent = 'Next';
  };

  const setStep = (step) => {
    currentStep = Math.min(Math.max(step, 1), totalSteps);
    stepElements.forEach((item) => {
      const stepNumber = Number(item.dataset.reportStep);
      item.classList.toggle('d-none', stepNumber !== currentStep);
    });
    stepIndicators.forEach((item) => {
      const stepNumber = Number(item.dataset.stepIndicator);
      item.classList.toggle('is-active', stepNumber === currentStep);
      item.classList.toggle('is-complete', stepNumber < currentStep);
    });
    if (prevBtn) prevBtn.disabled = currentStep === 1;
    if (nextBtn) nextBtn.classList.toggle('d-none', currentStep === totalSteps);
    if (submitBtn) submitBtn.classList.toggle('d-none', currentStep !== totalSteps);
    updateNextLabel();
    if (stepHint) {
      stepHint.textContent = `Step ${currentStep} of ${totalSteps}.`;
    }
    if (stepLabel) {
      stepLabel.textContent = getStepLabel(currentStep);
    }
    if (progressBar) {
      const progress = Math.round((currentStep / totalSteps) * 100);
      progressBar.style.width = `${progress}%`;
      if (progressContainer) {
        progressContainer.setAttribute('aria-valuenow', `${progress}`);
      }
    }
    if (currentStep === 2) {
      refreshMap();
    }
    if (currentStep === 3) {
      updateDraftPreview();
    }
    if (form.scrollIntoView) {
      form.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const validateStep = (step) => {
    const errors = [];

    if (step === 1) {
      if (!fullName.value.trim()) {
        errors.push('Full name is required.');
      }
      if (!phone.value.trim()) {
        errors.push('Phone number is required.');
      }
      if (email.value.trim() && email.checkValidity && !email.checkValidity()) {
        errors.push('Email address must be valid.');
      }
      if (!street.value.trim()) {
        errors.push('Street address is required.');
      }
      if (!city.value.trim()) {
        errors.push('City is required.');
      }
      if (!barangay.value.trim()) {
        errors.push('Area or neighborhood is required.');
      }
    }

    if (step === 2) {
      const latValue = parseFloat(latInput.value);
      const lngValue = parseFloat(lngInput.value);
      if (!hasUserSelected || Number.isNaN(latValue) || Number.isNaN(lngValue)) {
        errors.push('Select a location on the map to set coordinates.');
      }
      if (!mapsUrl.value.trim()) {
        if (!Number.isNaN(latValue) && !Number.isNaN(lngValue)) {
          updateMapsUrl(latValue, lngValue);
        } else {
          errors.push('Google Maps URL is required.');
        }
      }
    }

    if (step === 3) {
      if (!reportType.value.trim()) {
        errors.push('Report type is required.');
      }
      if (!description.value.trim()) {
        errors.push('Description is required.');
      }
    }

    if (errors.length) {
      showAlert('danger', errors);
      return false;
    }
    return true;
  };

  if (latInput && lngInput) {
    const handleCoordinateChange = () => {
      const latValue = parseFloat(latInput.value);
      const lngValue = parseFloat(lngInput.value);
      if (!Number.isNaN(latValue) && !Number.isNaN(lngValue)) {
        updateMapFromLatLng(latValue, lngValue, '', true);
      }
    };
    latInput.addEventListener('input', handleCoordinateChange);
    lngInput.addEventListener('input', handleCoordinateChange);
  }

  if (mapsUrl) {
    mapsUrl.addEventListener('input', () => {
      const parsed = parseLatLngFromUrl(mapsUrl.value);
      if (parsed) {
        updateMapFromLatLng(parsed.lat, parsed.lng, '', true);
      }
    });
  }

  [
    fullName,
    phone,
    email,
    street,
    barangay,
    city,
    addressNotes,
    reportType,
    description,
  ].forEach((field) => {
    if (!field) return;
    field.addEventListener('input', updateDraftPreview);
    field.addEventListener('change', updateDraftPreview);
  });

  if (dogMedia) {
    dogMedia.addEventListener('change', updateDraftPreview);
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
            updateMapFromLatLng(position.coords.latitude, position.coords.longitude, '', true);
            geoBtn.disabled = false;
            geoBtn.textContent = 'Use current location';
          },
          () => {
            showAlert('danger', 'Unable to access your location.');
            geoBtn.disabled = false;
            geoBtn.textContent = 'Use current location';
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

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      clearAlert();
      setStep(currentStep - 1);
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      clearAlert();
      if (validateStep(currentStep)) {
        setStep(currentStep + 1);
      }
    });
  }

  mapAvailable = initMap();
  setStep(currentStep);
  updateDraftPreview();

  const updateSummary = (payload, reportId) => {
    if (!summaryCard) return;
    if (summaryId) summaryId.textContent = reportId || '-';
    if (summaryStatus) summaryStatus.textContent = 'Pending';
    if (summaryType && reportType) {
      const selectedOption = reportType.options[reportType.selectedIndex];
      summaryType.textContent = selectedOption ? selectedOption.textContent : reportType.value;
    }
    if (summaryContact) summaryContact.textContent = payload.contact_name || '-';
    if (summaryPhone) summaryPhone.textContent = payload.contact_phone || '';
    if (summaryEmail) summaryEmail.textContent = payload.contact_email || '';
    if (summaryAddress) {
      const address = payload.location.address || {};
      const parts = [address.street, address.barangay, address.city].filter((part) => part);
      summaryAddress.textContent = parts.length ? parts.join(', ') : '-';
    }
    if (summaryAddressNotes) {
      summaryAddressNotes.textContent = payload.location.address?.notes || '';
    }
    if (summaryDescription) summaryDescription.textContent = payload.description || '-';
    const lat = Number(payload.location.lat);
    const lng = Number(payload.location.lng);
    if (summaryMap && !Number.isNaN(lat) && !Number.isNaN(lng)) {
      summaryMap.src = `https://maps.google.com/maps?q=${lat},${lng}&output=embed`;
    }
    if (summaryMedia) {
      summaryMedia.innerHTML = '';
      if (dogMedia && dogMedia.files && dogMedia.files[0]) {
        const file = dogMedia.files[0];
        const url = URL.createObjectURL(file);
        if (file.type.startsWith('video')) {
          const video = document.createElement('video');
          video.src = url;
          video.controls = true;
          summaryMedia.appendChild(video);
        } else if (file.type.startsWith('image')) {
          const img = document.createElement('img');
          img.src = url;
          img.alt = 'Reported dog media';
          summaryMedia.appendChild(img);
        }
      }
    }
    summaryCard.classList.remove('d-none');
  };

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearAlert();

    for (let step = 1; step <= totalSteps; step += 1) {
      if (!validateStep(step)) {
        setStep(step);
        return;
      }
    }

    const reportTypeValue = reportType.value.trim();
    const descriptionValue = description.value.trim();

    const latValue = parseFloat(latInput.value);
    const lngValue = parseFloat(lngInput.value);

    const payload = {
      report_type: reportTypeValue,
      description: descriptionValue,
      location_method: 'both',
      location: {
        lat: latValue,
        lng: lngValue,
        maps_url: mapsUrl.value.trim() || `https://maps.google.com/?q=${latValue},${lngValue}`,
        address: {
          street: street.value.trim(),
          barangay: barangay.value.trim(),
          city: city.value.trim(),
          notes: addressNotes.value.trim(),
        },
      },
      contact_name: fullName.value.trim(),
      contact_phone: phone.value.trim(),
      contact_email: email.value.trim(),
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
      updateSummary(payload, data.report_id);
      form.reset();
      setMapAddress('');
      hasUserSelected = false;
      clearMediaPreview(previewMedia);
      if (mapInstance && mapMarker) {
        updateMapFromLatLng(defaultCenter.lat, defaultCenter.lng, '', false);
      }
      setStep(1);
      updateDraftPreview();
    } catch (error) {
      showAlert('danger', 'Something went wrong. Please try again later.');
    } finally {
      submitBtn.disabled = false;
    }
  });
})();
