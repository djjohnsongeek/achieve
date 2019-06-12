import {reveal_error, button_error} from "./lib.js"

// listen for form submission
document.getElementById("btn_update_class").addEventListener("click", function(event){

// prevent submission
    event.preventDefault();
    var button = document.getElementById("btn_update_class");
    var class_name = document.getElementById("slct_class");

    if (!class_name.value)
    {
        class_name.style.border = "1px solid red";
        button_error(button);
    }
    else
    {
        class_name.style.border = "1px solid grey";
        document.getElementById("form_update_class").submit();
    }
});