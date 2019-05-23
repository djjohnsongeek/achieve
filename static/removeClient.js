var client_name = document.getElementById("slct_client");

//Listen for the button being clicked
document.getElementById("btn_remove_client").addEventListener("click", function(event){

//prevent form submission
    event.preventDefault();
    console.log("prevented submission");
    if (!client_name.value)
    {
        client_name.style.border = "2px solid red";
    }
    else
    {
        client_name.style.border = "1px solid grey";
        document.getElementById("form_remove_client").submit()
    }
});