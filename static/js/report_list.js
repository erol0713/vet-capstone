(() => {
  const modal = document.getElementById('reportViewModal');
  if (!modal) return;

  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = value || '-';
    }
  };

  const mapWrap = document.getElementById('reportModalMap');
  const mapFrame = document.getElementById('reportModalMapFrame');
  const mediaWrap = document.getElementById('reportModalMedia');
  const mediaImage = document.getElementById('reportModalImage');
  const mediaVideo = document.getElementById('reportModalVideo');

  const showMap = (lat, lng) => {
    if (!mapWrap || !mapFrame) return;
    mapFrame.src = `https://maps.google.com/maps?q=${lat},${lng}&output=embed`;
    mapWrap.classList.remove('d-none');
  };

  const hideMap = () => {
    if (!mapWrap || !mapFrame) return;
    mapFrame.removeAttribute('src');
    mapWrap.classList.add('d-none');
  };

  const showMedia = (url, kind) => {
    if (!mediaWrap || !mediaImage || !mediaVideo) return;
    mediaWrap.classList.remove('d-none');
    if (kind === 'video') {
      mediaVideo.src = url;
      mediaVideo.classList.remove('d-none');
      mediaImage.classList.add('d-none');
    } else {
      mediaImage.src = url;
      mediaImage.classList.remove('d-none');
      mediaVideo.classList.add('d-none');
      mediaVideo.removeAttribute('src');
    }
  };

  const hideMedia = () => {
    if (!mediaWrap || !mediaImage || !mediaVideo) return;
    mediaWrap.classList.add('d-none');
    mediaImage.removeAttribute('src');
    mediaVideo.removeAttribute('src');
    mediaImage.classList.add('d-none');
    mediaVideo.classList.add('d-none');
  };

  modal.addEventListener('show.bs.modal', (event) => {
    const button = event.relatedTarget;
    if (!button) return;
    const data = button.dataset;

    setText('reportModalId', data.reportId);
    setText('reportModalType', data.reportType);
    setText('reportModalStatus', data.reportStatus);
    setText('reportModalLocation', data.reportLocation);
    setText('reportModalSubmitted', data.reportSubmitted);
    setText('reportModalDescription', data.reportDescription);

    const lat = parseFloat(data.reportLat);
    const lng = parseFloat(data.reportLng);
    if (!Number.isNaN(lat) && !Number.isNaN(lng)) {
      showMap(lat, lng);
    } else {
      hideMap();
    }

    if (data.reportPhotoUrl) {
      showMedia(data.reportPhotoUrl, data.reportPhotoKind || 'image');
    } else {
      hideMedia();
    }
  });

  modal.addEventListener('hidden.bs.modal', () => {
    hideMap();
    hideMedia();
  });
})();
