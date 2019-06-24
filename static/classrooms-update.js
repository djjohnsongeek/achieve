import {button_error, validate} from "./lib.js"

// listen for form submission
document.getElementById("btn_update_class").addEventListener("click", function(event){

// prevent submission
    event.preventDefault();
    var button = document.getElementById("btn_update_class");
    var class_name = document.getElementById("slct_class");
    var times = [document.getElementById("class_hours_update_start"), document.getElementById("class_hours_update_end")];

    if (!class_name.value)
    {
        class_name.style.border = "1px solid red";
        button_error(button);
    }

    else if (times[0].value && times[1].value)
    {
        if(!validate(times))
        {
            button_error(button)
        }
        else
        {
            class_name.style.border = "1px solid grey";
            document.getElementById("form_update_class").submit();
        }
    }

    else
    {
        class_name.style.border = "1px solid grey";
        document.getElementById("form_update_class").submit();
    }
});