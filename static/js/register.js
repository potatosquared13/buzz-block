function displayForm() {

  document.getElementById('form-container').style.pointerEvents = "all";
  document.getElementById('form-container').style.margin = "5% auto";
  document.getElementById('form-container').style.opacity = "1";

}

function hideForm() {

  document.getElementById('form-container').style.pointerEvents = "all";
  document.getElementById('form-container').style.margin = "0% auto";
  document.getElementById('form-container').style.opacity = "0";

}

function addClient() {

  let username = document.getElementById('username').value;
  let amount = document.getElementById('password').value;
  let url = `/register?username=${username}&amount=${amount}`;

  let xhr = new XMLHttpRequest();

  xhr.onreadystatechange = () => {

    if (xhr.readyState == 4 && xhr.status == 200) {
      hideForm();
    }

  }

  xhr.open('POST', url, true);
  xhr.send()

}