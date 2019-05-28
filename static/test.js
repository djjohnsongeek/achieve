//validate function
function validate(forms)
{
    var valid =  true;
    for (i = 0; i <forms.length; i++)
    {
        if (!forms[i].value)
        {   
            var valid = false;
            forms[i].style.border = "2px solid red"
        }
        else
        {
            forms[i].style.border = "1px solid grey"
        }
    }
    return valid
}

//Listen for the button being clicked
document.getElementById("btn_add_client").addEventListener("click", function(event){

    // store client first and last name in variable
    var client_name = document.getElementById("client_name");
    var hrsForms = [client_name, document.getElementById("client_hours_start"), document.getElementById("client_hours_end")];

//prevent form submission
    event.preventDefault();
    console.log("prevented submission");
    console.log(client_name.value);

    //send GET request with clientname
    $.get("/addclient?clientname=" + client_name.value, function(data){
        console.log(data);
        if (data == false)
        {
            if (validate(hrsForms))
            {
                document.getElementById("form_add_client").submit();
            }
        }
        else
        {
            alert("This Client already exists in the database");
        }
    });
});