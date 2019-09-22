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

  xhr.open('GET', '/check_transactions_changed', true);
  xhr.send();

}