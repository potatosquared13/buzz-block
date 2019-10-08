var checkInterval = null;

window.onload = () => {
  checkIfNodeToggled();
}

function toggleNode(e) {
  let xhr = new XMLHttpRequest();
  xhr.open('GET', '/toggle', true);
  xhr.send();
  checkIfNodeToggled();
}

function checkTransactionsChanged() {
  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = () => {
    if (xhr.readyState == 4 && xhr.status == 200) {
      if (xhr.responseText == 'good') {
        window.location.href = '/transactions'
      }
    }
  }
  xhr.open('POST', '/check_transactions_changed', true);
  xhr.send();
}

function checkIfNodeToggled() {
  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = () => {
    if (xhr.readyState == 4 && xhr.status == 200) {
      if (xhr.responseText == '1') {
        document.getElementById("node-status").checked = true;
        checkInterval = setInterval(checkTransactionsChanged, 4000);
      } else {
        document.getElementById("node-status").checked = false;
        clearInterval(checkInterval);
      }
    }
  }
  xhr.open('GET', '/check_toggle', true);
  xhr.send();
}