import {validate, reveal_error} from "./lib.js"

// listen for add staff button
document.getElementById("btn_add_staff").addEventListener("click", function(event){
    event.preventDefault();
    var button = document.getElementById("btn_add_staff");
    var staff_name = document.getElementById("staff_name");
    var requiredFields = [staff_name, document.getElementById("staff_hours_start"), document.getElementById("staff_hours_end")]
    if (validate(requiredFields))
    {
        document.getElementById("form_add_staff").submit();
    }
    else
    {
        var original_text = button.innerText;
        button.style.backgroundColor = "red";
        button.innerText = "Check for Errors";
        setTimeout(reveal_error, 3000, button, original_text);
    }
});

// listen for remove staff button
document.getElementById("btn_remove_staff").addEventListener("click", function(event){
    event.preventDefault();
    var button = document.getElementById("btn_remove_staff");
    var staff_name = document.getElementById("slct_staff_remove");

    if (!staff_name.value)
    {
        staff_name.style.border = "1px solid red";
        var original_text = button.innerText;
        button.style.backgroundColor = "red";
        button.innerText = "Check for Errors";
        setTimeout(reveal_error, 1500, button, original_text);
    }
    else
    {
        document.getElementById("form_remove_staff").submit();
    }
})