window.onload = () => {

  setInterval(() => {

  }, 1000);

}

function checkTransactionsChanged() {

  let xhr = new XMLHttpRequest();

  xhr.open('GET', '/check_transactions_changed', true);
  xhr.send();

}