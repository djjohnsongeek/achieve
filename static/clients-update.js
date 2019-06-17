import {reveal_error, button_error, validate} from "./lib.js"

//Listen for update client info button being clicked
document.getElementById("btn_update_client").addEventListener("click", function(event){

    //prevent form submission
    event.preventDefault();

    var client_name = document.getElementById("slct_update_client");
    var hrsForms = [document.getElementById("new_client_hours_start"), document.getElementById("new_client_hours_end")];
    var button = document.getElementById("btn_update_client");

    // reset error colors:
    client_name.style.border = "";

    if (client_name.value)
    {
        if (hrsForms[0].value && hrsForms[1].value)
        {
            if(validate(hrsForms))
            {
                document.getElementById("form_update_client").submit();
            }
            else
            {
                button_error(button);
            }
        }
        else
        {
            document.getElementById("form_update_client").submit();
        }
    }
    else
    {
        button_error(button);
        client_name.style.border = "1px solid red";
    }
});