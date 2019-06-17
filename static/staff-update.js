import {reveal_error, button_error, validate} from "./lib.js"

// listen for update staff button
document.getElementById("btn_update_staff").addEventListener("click", function(event){
    event.preventDefault();
    var button = document.getElementById("btn_update_staff");
    var staff_name = document.getElementById("slct_staff_update");
    var hrsForms = [document.getElementById("staff_hours_update_start"), document.getElementById("staff_hours_update_end")];

    // reset name field's border
    staff_name.style.border = "";

    if (!staff_name.value)
    {
        staff_name.style.border = "1px red solid";
        button_error(button);
    }
    else
    {
        if (hrsForms[0].value && hrsForms[1].value)
        {
            if (validate(hrsForms))
            {
                document.getElementById("form_update_staff").submit();
            }
            else
            {
                button_error(button);
            }
        }
        else
        {
            document.getElementById("form_update_staff").submit();
        }
    }
});