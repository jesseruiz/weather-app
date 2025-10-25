import { Amplify } from 'aws-amplify';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolClientId: '2a8pb3di16qi3t8p265idm9k12',
      userPoolId: 'us-east-1_0c1i9TA7N',
    }
  }
});
