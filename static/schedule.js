import {reveal_error} from "./lib.js"

// listen for form submission
document.getElementById("btn_generate").addEventListener("click", function(event){
    //prevent submission
    event.preventDefault();
    var button = document.getElementById("btn_generate");
    var weekDay = document.getElementById("slct_schedule_day");

    if (!weekDay.value)
    {
        weekDay.style.border = "1px solid red";
        var original_text = button.innerText;
        button.style.backgroundColor = "red";
        button.innerText = "Select a day";
        setTimeout(reveal_error, 1000, button, original_text)
    }
    else
    {
        weekDay.style.border = "1px solid grey";
        document.getElementById("schedule_day").submit();
    }
});