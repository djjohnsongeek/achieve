import {validate, reveal_error, button_error} from "./lib.js"

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
        button_error(button);
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
        button_error(button);
    }
    else
    {
        document.getElementById("form_remove_staff").submit();
    }
})