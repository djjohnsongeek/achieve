import {reveal_error, button_error, validate} from "./lib.js"

// listen for generate_sch button
document.getElementById("btn_create_sch").addEventListener("click", function(event){
    //prevent submission
    event.preventDefault();
    var button = document.getElementById("btn_create_sch");
    var weekDay = document.getElementById("slct_schedule_day");

    if (!weekDay.value)
    {
        weekDay.style.border = "1px solid red";
        button_error(button);
    }
    else
    {
        weekDay.style.border = "1px solid grey";
        document.getElementById("schedule_day").submit();
    }
});

// listen for download button
document.getElementById("btn_download").addEventListener("click", function(event){
    event.preventDefault();
    var button = document.getElementById("btn_download");
    var download_options = [document.getElementById("slct_download_day"), document.getElementById("slct_schedule_type")];

    if (validate(download_options))
    {
        document.getElementById("form_download_sch").submit();
    }
    else
    {
        button_error(button);
    }
});

// listen for schedule backup button
document.getElementById("btn_manage_db").addEventListener("click", function(event){
    event.preventDefault();
    var db_option = [document.getElementById("slct_db_backup")];
    var button = document.getElementById("btn_manage_db");

    if (validate(db_option))
    {
        document.getElementById("form_manage_db").submit();
    }
    else
    {
        button_error(button);
    }
});