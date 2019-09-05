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

function finalize() {

  /*let xhr = new XMLHttpRequest();

  xhr.onreadystatechange = () => {

    if (xhr.readyState == 4 && xhr.status == 200) {

      document.getElementById('non-vendor-register').disabled = true;
      document.getElementById('vendor-register').disabled = true;

    }

  }

  xhr.open('GET', '/finalize', true);
  xhr.send();*/

  window.location.href = '/finalize';

}