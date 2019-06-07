import {reveal_error} from "./lib.js"

//Listen for update client info button being clicked
document.getElementById("btn_update_client").addEventListener("click", function(event){
    //prevent form submission
    event.preventDefault();
    var client_name = document.getElementById("slct_update_client");
    var button = document.getElementById("btn_update_client");
    if (!client_name.value)
    {
        client_name.style.border = "1px solid red";
        var original_text = button.innerText;
        button.style.backgroundColor = "red";
        button.innerText = "Check for Errors";
        setTimeout(reveal_error, 3000, button, original_text);
    }
    else
    {
        client_name.style.border = "1px solid grey";
        document.getElementById("form_update_client").submit();
    }
});