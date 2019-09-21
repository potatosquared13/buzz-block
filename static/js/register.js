let clients = 0;

window.onload = () => {

  let client_table = document.getElementById('client-data');

  let client_rows = client_table.getElementsByTagName('tr');

  clients = client_rows.length;

  alert(clients);

}

function addNonVendor() {

  let name = document.getElementById('non-vendor-name').value;
  let amount = document.getElementById('amount').value;
  let contactNumber = document.getElementById('non-vendor-contact-number').value;
  let url = `/register?clientId=${clients}&name=${name}&amount=${amount}&contactNumber=${contactNumber}&isVendor=0`;

  let xhr = new XMLHttpRequest();

  xhr.onreadystatechange = () => {

    if (xhr.readyState == 4 && xhr.status == 200) {
      
      document.getElementById('client-data').innerHTML += `
      
        <tr>
          <td>${clients}</td>
          <td>NV</td>
          <td>${name}</td>
          <td>${contactNumber}</td>
          <td>${amount}</td>
        </tr>
      
      `;

      clients++;

    }

  }

  xhr.open('POST', url, true);
  xhr.send()

}

function addVendor() {

  let name = document.getElementById('vendor-name').value;
  let contactNumber = document.getElementById('vendor-contact-number').value;
  let url = `/register?clientId=${clients}&name=${name}&amount=0&contactNumber=${contactNumber}&isVendor=1`;

  let xhr = new XMLHttpRequest();

  xhr.onreadystatechange = () => {

    if (xhr.readyState == 4 && xhr.status == 200) {
      
      document.getElementById('client-data').innerHTML += `
      
        <tr>
          <td>${clients}</td>
          <td>V</td>
          <td>${name}</td>
          <td>${contactNumber}</td>
          <td>0</td>
        </tr>
      
      `;

      clients++;

    }

  }

  xhr.open('POST', url, true);
  xhr.send()

}

function getClients() {

  let xhr = new XMLHttpRequest();

  xhr.onreadystatechange = () => {

    let clientTable = document.getElementById('client-data');

    clientTable.innerHTML += `
    
      <tr>
      
        <td>${placeholder}</td>
        <td>${placeholder}</td>
        <td>${placeholder}</td>
        <td>${placeholder}</td>
        <td>${placeholder}</td>
      
      </tr>
    
    `


  }

  xhr.open('GET', '/get-clients', true);
  xhr.send();

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