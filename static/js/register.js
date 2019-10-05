function registerClient() {

  let name = document.getElementById('client-name').value;
  let amount = document.getElementById('client-amount').value;
  let contactNumber = document.getElementById('client-contact').value;
  let url = `/register_client?name=${name}&amount=${amount}&contact=${contactNumber}`;

  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = () => {
    if (xhr.readyState == 4 && xhr.status == 200) {
        window.location.href = '/'
    }
  }
  xhr.open('POST', url, true);
  xhr.send()

  name = document.getElementById('client-name').value = "";
  amount = document.getElementById('client-amount').value = "";
  contactNumber = document.getElementById('client-contact').value = "";
}

function registerVendor() {
  let name = document.getElementById('vendor-name').value;
  let contactNumber = document.getElementById('vendor-contact').value;
  let type = document.getElementById('vendor-type').value;
  let url = `/register_vendor?name=${name}&contact=${contactNumber}&type=${type}`;

  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = () => {
    if (xhr.readyState == 4 && xhr.status == 200) {
        window.location.href = '/'
    }
  }
  xhr.open('POST', url, true);
  xhr.send()

  document.getElementById('vendor-name').value = "";
  document.getElementById('vendor-contact').value = "";
  document.getElementById('vendor-type').value = "";
}

function finalize() {
  window.location.href = '/finalize';
}

function addFunds(identity) {
  while(isNaN(amount = window.prompt("Enter an amount", "")));
  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = () => {
    if (xhr.readyState == 4 && xhr.status == 200) {
        window.location.href = '/'
    }
  }
  xhr.open('POST', `/add_funds?identity=${identity}&amount=${amount}`, true);
  xhr.send()
}

function blacklist(name, current_id, amount) {
    if (window.confirm("Blacklist user's current id?\nA new id will be generated for this user.\nWARNING: THIS CANNOT BE UNDONE.")) {
      let xhr = new XMLHttpRequest();
      xhr.onreadystatechange = () => {
        if (xhr.readyState == 4 && xhr.status == 200) {
            window.location.href = '/'
        }
      }
      xhr.open('POST', `/register_client?replace=true&identity=${current_id}&name=${name}&amount=${amount}`, true);
      xhr.send()
    }
}

function isEmpty(str){
  return !str.replace(/\s+/, '').length;
}

function checkClient(event) {
  name = document.getElementById("client-name").value;
  contact = document.getElementById("client-contact").value;
  amount = document.getElementById("client-amount").value;
  if (isEmpty(name) || isEmpty(contact) || isEmpty(amount) || isNaN(amount) || parseFloat(amount) == 0) {
    if (!document.getElementById("client-add").disabled) {
      document.getElementById("client-add").disabled = true;
    }
  } else {
    if (document.getElementById("client-add").disabled) {
      document.getElementById("client-add").disabled = false;
    }
  }
}

function checkVendor(event) {
  name = document.getElementById("vendor-name").value;
  contact = document.getElementById("vendor-contact").value;
  type = document.getElementById("vendor-type").value;
  if (isEmpty(name) || isEmpty(contact) || isEmpty(type)) {
    if (!document.getElementById("vendor-add").disabled) {
      document.getElementById("vendor-add").disabled = true;
    }
  } else {
    if (document.getElementById("vendor-add").disabled) {
      document.getElementById("vendor-add").disabled = false;
    }
  }
}