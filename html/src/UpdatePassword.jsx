import { AccountSettings } from '@aws-amplify/ui-react';

export default function UpdatePassword(){

    const handleSuccess = () => {
        alert('password is successfully changed!')
    }

    return(
        <div className='UpdatePassword'>
            <h3>Update Password</h3>
            <AccountSettings.ChangePassword onSuccess={handleSuccess}/>
        </div>

    );
}