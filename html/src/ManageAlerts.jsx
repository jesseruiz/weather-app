import { Checkbox, useAuthenticator } from '@aws-amplify/ui-react';


export default function ManageAlerts() {
    const { authStatus, user } = useAuthenticator((authState) => [authState.authStatus, authState.user]);


    return (
      <div className="manage_alerts">
        <div>
            <h2>Manage Weather Alerts</h2>
        </div>
        <div>
            <p>City is: city</p>
            <button>Update City</button>
        </div>
        <div>
            <p>Email?</p>
            <p>Text?</p>
            <p>Frequency</p>
            <p>Dropdown with "Only new events", "Daily", "Weekly"</p>
        </div>
      </div>
    );
  }