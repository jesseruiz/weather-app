import { AccountSettings } from '@aws-amplify/ui-react';
import './UpdatePassword.css';

export default function UpdatePassword(){

    const handleSuccess = () => {
        alert('password is successfully changed!')
    }

    return(
        <div className="update-password">
            <h3>Update Password</h3>
            <AccountSettings.ChangePassword onSuccess={handleSuccess}/>
        </div>

    );
}