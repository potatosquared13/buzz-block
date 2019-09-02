window.onload = () => {
  showForm();
}

function addNonVendor() {

  let name = document.getElementById('non-vendor-name').value;
  let amount = document.getElementById('amount').value;
  let contactNumber = document.getElementById('non-vendor-contact-number').value;
  let url = `/register?name=${name}&amount=${amount}&contactNumber=${contactNumber}&isVendor=0`;

  let xhr = new XMLHttpRequest();

  xhr.open('POST', url, true);
  xhr.send()

}

function addVendor() {

  let name = document.getElementById('vendor-name').value;
  let contactNumber = document.getElementById('vendor-contact-number').value;
  let url = `/register?name=${name}&amount=0&contactNumber=${contactNumber}&isVendor=1`;

  let xhr = new XMLHttpRequest();

  xhr.open('POST', url, true);
  xhr.send()

}

function showForm() {

  document.getElementById('form-container').style.display = "block";
  document.getElementById('transactions-container').style.display = "none";

}

function showTransactions() {

  document.getElementById('form-container').style.display = "none";
  document.getElementById('transactions-container').style.display = "block";

}