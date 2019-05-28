// listen for form submission
document.getElementById("btn_generate").addEventListener("click", function(event){
    //prevent submission
    event.preventDefault();
    var weekDay = document.getElementById("slct_schedule_day");

    if (!weekDay.value)
    {
        weekDay.style.border = "1px solid red";
    }
    else
    {
        weekDay.style.border = "1px solid grey";
        document.getElementById("schedule_day").submit();
    }
});