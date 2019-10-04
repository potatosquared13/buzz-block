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
  xhr.open('POST', `/add_funds?identity=${identity}&amount=${amount}`, true);
  xhr.send()
}

function blacklist(name, current_id) {
    if (window.confirm("Blacklist user's current id?\nA new id will be generated for this user.")) {
      let xhr = new XMLHttpRequest();
      xhr.open('POST', `/register_client?replace=true&identity=${current_id}&name=${name}`, true);
      xhr.send()
    }
}