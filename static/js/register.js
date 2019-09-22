function registerClient() {

  let name = document.getElementById('client-name').value;
  let amount = document.getElementById('client-amount').value;
  let contactNumber = document.getElementById('client-contact').value;
  let url = `/register_client?name=${name}&amount=${amount}&contact=${contactNumber}`;

  let xhr = new XMLHttpRequest();

  xhr.open('POST', url, true);
  xhr.send()

}

function registerVendor() {

  let name = document.getElementById('vendor-name').value;
  let contactNumber = document.getElementById('vendor-contact').value;
  let url = `/register_vendor?name=${name}&contact=${contactNumber}`;

  let xhr = new XMLHttpRequest();

  xhr.open('POST', url, true);
  xhr.send()

}

function finalize() {
  window.location.href = '/finalize';
}