// store client first and last name in variable
var client_name = document.getElementById("client_name");

//Listen for the button being clicked
document.getElementById("btn_add_client").addEventListener("click", function(event){

//prevent form submission
    event.preventDefault();
    console.log("prevented submission");
    //send GET request with clientname
    $.get("/addclient?clientname=" + client_name.value, function(data){
        console.log(data);
        if (data == true)
        {
            document.getElementById("form_add_client").submit();
        }
        else
        {
            alert("Client Name already Exists")
        }
    });
});