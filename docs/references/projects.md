## **Introduction**

The project is the enhanced version of a submission. A project can be created only after the `Accepted` state(approved by staff) of a submission. It is a process to review the legalities of an application(PAF), get applicant details(like bank details and etc), and avail the funds to an applicant via contracts and invoices. We will learn more about its terminology, workflow, usage, and implementation below. First, Let's start with its terminology.

## **Terminology**

There are a few terms that are a bit strict to its business logic like Project Approval Form(PAF), Contracts, and Invoices.

### **KeyTerms**
1. **Project**: A project is just like another form of submission but one level above to the submission, which holds most of the information and acts like a basic and most important entity for the funding. 
2. **Project Approval Form(PAF)**: PAF is an extended version of the Project. It is a stream form generated via the wagtail dashboard and attach to the respective fund. It is generally responsible for legal questions' answers by staff. It has to be approved by PAFReviewerRoles(needs to add in Project Settings, wagtail dashboard) and then require final approval by contracting+approval role. PAFReviewerRoles are generally compliance attorneys, staff members, or finance members.
3. **Contract**: It is an updated version of the downloaded approved PAF with some changes/updates by contracting(role) members that have to be downloaded and signed by the contractor/project user(owner) and upload back to the system. Then it can be approved by staff members.
4. **Invoice**: Invoice is self-explanatory, it will help applicants to get the fund against their applications. Invoices also have to go through multiple approvals like staff approval, and finance approval.


## Workflow

**Project statuses**: Commited -> Waiting for approval -> Contracting -> In Progress -> Closing -> Complete

1. **Commited**: It is the first stage of a project. When a submission gets approved or converted into a project, the project automatically gets into its first state called `Commited`. Now, 'Vendor Form' and 'Project Approval Form' needs to be checked or filled by the staff members and there are optional 'Supporting Documents' section as well where staff members can upload the required or optional documents. Now a lead or any other staff member can send a project for approval(Send For Approval) and the project status will get changed to `Waiting For Approval`. 
2. **Waiting for Approval**: It is the status when 'PAFReviewerRoles' have to review the PAF and after their approvals, the project requires final approval by contracting+approver roles. PAFReviewerRoles are the virtual/wrapper roles over staff members, contracting members, and finance members. PAFReviewerRoles can be added/changed in 'ProjectSettings' via the admin dashboard. These roles are interchangeable, which means one user(from the above groups)/PAFReviewerRole can review things on behalf of other users/PAFReviewerRoles(if there are multiple PAFReviewerRoles). We keep the record of who is reviewing the PAF on whose behalf or for which PAFReviewerRole.
Ex: Assume that PAFReviewer1 and PAFReviewer2 are two roles set in the wagtail dashboard. So now a PAF has to be approved by these two roles. And assume user_s is a staff member, user_c is a contracting member, and user_f is a finance member. Now, any user(user_s or user_c or user_f) can review/approve the PAF as PAFReviewer1 and PAFReviewer2. As we record the actions so it is safe and can be tracked easily, also all these user groups are trustworthy and the org's employees.
After their approval, a notification will be sent to the contracting group email(Shouldn't we send it to that role only?) so that contracting+approver roles can approve the Project. After the final approval, the project's status will get changed to `Contracting`.
3. **Contracting**: After approval of a PAF, the attorney or staff member can download the approved PAF and can upload it back as a contract by updating(optional) a few things in it. Then it can be downloaded and signed by the applicant or a staff member can also upload a signed contract directly. Now Staff member has to review and approve the contract. After contract approval, the project's status will get changed to `In Progress`.  (Can a contracting member upload a contract?)
4. **In Progress**: In this status, an applicant or a staff member can add invoices and reports to the system. An invoice has to be approved by staff members and then by the finance department(finance1 and finance2, in some cases). 
5. **Closing**:
6. **Complete**:

### **Related User or Users' Group**
1. Contractor/Applicant
2. Staff (PM, VP)
3. Finance
4. Contracting (compliance attorneys)
5. Contracting + Approver (PAF's final approver)
