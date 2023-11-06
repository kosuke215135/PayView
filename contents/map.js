function initMap() {
  // Create the map.
  const map = new google.maps.Map(document.getElementById('map'), {
    zoom: 14,
    center: {lat: 26.25317678396155, lng: 127.76585529789524},
  });

  // Load the stores GeoJSON onto the map.
  map.data.loadGeoJson('stores.json', {idPropertyName: 'storeid'});

  const apiKey = 'AIzaSyDgVJBWiiCC8qEXIvLcLeOatB1jG6oewnE';
  const infoWindow = new google.maps.InfoWindow();

  // Show the information for a store when its marker is clicked.
  map.data.addListener('click', (event) => {
    const category = event.feature.getProperty('category');
    const name = event.feature.getProperty('name');
    const description = event.feature.getProperty('description');
    const hours = event.feature.getProperty('hours');
    const phone = event.feature.getProperty('phone');
    const position = event.feature.getGeometry().get();
    const content = `
      <h2>${name}</h2><p>${description}</p>
      <p><b>Open:</b> ${hours}<br/><b>Phone:</b> ${phone}</p>
    `;

    infoWindow.setContent(content);
    infoWindow.setPosition(position);
    infoWindow.setOptions({pixelOffset: new google.maps.Size(0, -30)});
    infoWindow.open(map);
  });

// Build and add the search bar
const card = document.createElement('div');
const titleBar = document.createElement('div');
const title = document.createElement('div');
const container = document.createElement('div');
const input = document.createElement('input');
const options = {
types: ['address'],
componentRestrictions: {country: 'gb'},
};

card.setAttribute('id', 'pac-card');
title.setAttribute('id', 'title');
title.textContent = 'Find the nearest store';
titleBar.appendChild(title);
container.setAttribute('id', 'pac-container');
input.setAttribute('id', 'pac-input');
input.setAttribute('type', 'text');
input.setAttribute('placeholder', 'Enter an address');
container.appendChild(input);
card.appendChild(titleBar);
card.appendChild(container);
map.controls[google.maps.ControlPosition.TOP_RIGHT].push(card);

// Make the search bar into a Places Autocomplete search bar and select
// which detail fields should be returned about the place that
// the user selects from the suggestions.
const autocomplete = new google.maps.places.Autocomplete(input, options);

autocomplete.setFields(
  ['address_components', 'geometry', 'name']);
}