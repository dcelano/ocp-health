# OCP external node check and recover

## Provision a service account

To create a service account in OpenShift to query the /api/v1/nodes/ API endpoint, you can follow these steps:

Log in to the OpenShift cluster using the oc command-line tool. You will need to have the oc tool installed on your machine and be logged in as a user with sufficient permissions to create a service account.

Run the following command to create a new service account:

```bash
oc create serviceaccount <service-account-name>
```

Replace **service-account-name** with a name for the service account.

Run the following command to grant the service account the view role on the nodes resource:

```bash
oc adm policy add-cluster-role-to-user cluster-reader \
system:serviceaccount:<namespace>:<service-account-name>
```

Replace **service-account-name** with the name of the service account you created in step 2, and **namespace** with the namespace where the nodes are located.

Run the following command to retrieve the token name for the service account:

```bash
oc describe serviceaccount <service-account-name> -n <namespace> | grep Tokens | awk '{print $2}'
```

Replace **service-account-name** with the name of the service account, and **namespace** with the namespace where the service account was created. This command will output the token for the service account.

Run the following command to retrieve the token value from the associated secret:

```bash
oc describe secret <token-name> -n <namespace>
```

Replace **token-name** with the name of the token, and **namespace** with the namespace where the service account was created.