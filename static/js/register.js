function registerClient() {

  let name = document.getElementById('client-name').value;
  let amount = document.getElementById('client-amount').value;
  let contactNumber = document.getElementById('client-contact').value;
  let url = `/register_client?name=${name}&amount=${amount}&contact=${contactNumber}`;

  let xhr = new XMLHttpRequest();

  xhr.open('POST', url, true);
  xhr.send()

  name = document.getElementById('client-name').value = "";
  amount = document.getElementById('client-amount').value = "";
  contactNumber = document.getElementById('client-contact').value = "";
}

function registerVendor() {

  let name = document.getElementById('vendor-name').value;
  let contactNumber = document.getElementById('vendor-contact').value;
  let url = `/register_vendor?name=${name}&contact=${contactNumber}`;

  let xhr = new XMLHttpRequest();

  xhr.open('POST', url, true);
  xhr.send()

  name = document.getElementById('vendor-name').value = "";
  contactNumber = document.getElementById('vendor-contact').value = "";
}

function finalize() {
  window.location.href = '/finalize';
}

function editClient() {
  document.getElementById('client-edit').classList.add("hidden");
  document.getElementById('cancel-edit').classList.add("hidden");
  document.getElementById('client-add').classList.remove("hidden");

  document.getElementById('client-name').disabled = false;
  document.getElementById('client-contact').disabled = false;

  // call registerClient() i guess
}

function cancelEdit() {
  document.getElementById('client-edit').classList.add("hidden");
  document.getElementById('cancel-edit').classList.add("hidden");
  document.getElementById('client-add').classList.remove("hidden");
  document.getElementById('client-name').disabled = false;
  document.getElementById('client-contact').disabled = false;
  document.getElementById('client-name').value = "";
  document.getElementById('client-contact').value = "";
  document.getElementById('client-amount').value = "";
}

function addFunds() {
  amount = window.prompt("Enter an amount", 0);
  // do stuff
  // call function/route in app.py to add funds
}

function blacklist() {
  // get user information from table row
  // document.getElementById('client-name').value = name;
  // document.getElementById('client-amount').value = amount;
  // document.getElementById('client-contact').value = contact;

  document.getElementById('client-add').classList.add("hidden");
  document.getElementById('client-edit').classList.remove("hidden");
  document.getElementById('cancel-edit').classList.remove("hidden");

  document.getElementById('client-name').disabled = true;
  document.getElementById('client-contact').disabled = true;
}