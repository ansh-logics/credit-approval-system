import dotenv from "dotenv";


dotenv.config()

let registerPage = () =>{
   let BASE_URL = process.env.BACKEND_URL;
   
   return (
    <>
        <form action="submit">
            <input type="text" name="first_name" id="firstName" className="nameInput"  placeholder="John"/>
            <input type="text" name="last_name" id= "lastName" className="nameInput" placeholder="Doe"/>
            <input type="number" name="age" id="age" className="age" placeholder="69"/>
            <input type="number"  name="income" id="income" className="income" placeholder="70000000"/>
            <input type="text" name="phoneNumber" id="phoneNumber" className="phoneNumber" placeholder="2223334445" />
        </form> 
    </>
   )
 
};