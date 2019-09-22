window.onload = () => {
  setInterval(checkTransactionsChanged, 1000);
}

function toggleNode() {

  let xhr = new XMLHttpRequest();

  xhr.open('GET', '/toggle', true);
  xhr.send();

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