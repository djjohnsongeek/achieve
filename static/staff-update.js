import {reveal_error} from "./lib.js"

// listen for update staff button
document.getElementById("btn_update_staff").addEventListener("click", function(event){
    event.preventDefault();
    var button = document.getElementById("btn_update_staff");
    var staff_name = document.getElementById("slct_staff_update");

    if (!staff_name.value)
    {
        staff_name.style.border = "1px red solid";
        var original_text = button.innerText;
        button.style.backgroundColor = "red";
        button.innerText = "Check for Errors";
        setTimeout(reveal_error, 2000, button, original_text);
    }
    else
    {
        staff_name.style.border = "1px grey solid";
        document.getElementById("form_update_staff").submit();
    }
});