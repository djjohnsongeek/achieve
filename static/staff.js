import {validate, button_error} from "./lib.js"

// listen for add staff button
document.getElementById("btn_add_staff").addEventListener("click", function(event){

    var button = document.getElementById("btn_add_staff");
    var staff_name = document.getElementById("staff_name");
    var requiredFields = [staff_name, document.getElementById("staff_hours_start"), document.getElementById("staff_hours_end")]

    // reset default look
    document.getElementById("staff_name_title").innerHTML = "Add Staff";
    document.getElementById("staff_name_title").style.color = "#212962";
    staff_name.style.border = "1px solid grey";

    event.preventDefault();
    // send get request
    $.get("/addStaff?staffname=" + staff_name.value, function(data){
        if (data == false)
        {
            if (validate(requiredFields))
            {
                document.getElementById("form_add_staff").submit();
            }
            else
            {
                button_error(button);
            }
        }
        else
        {
            //style header
            document.getElementById("staff_name_title").innerHTML = "Staff Already Exists";
            document.getElementById("staff_name_title").style.color = "red";
            staff_name.style.border = "1px solid red";
            button_error(button);
        }
    });
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