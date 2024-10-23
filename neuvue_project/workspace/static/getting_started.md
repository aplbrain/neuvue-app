# Getting Started with Neuvue

This page contains resources and documentation to help you get started proofreading on NeuVue. For any questions or comments, please reach out to the NeuVue development team on slack or email daniel.xenes@jhuapl.edu.

## Accessing the Proofreading Interface

### Home Page

<img src="https://i.imgur.com/BbuuTWg.png" alt="Home Page" width="800"/>

NeuVue's main home page will be always located at app.neuvue.io. To make the login process seamless, we use google sign-on service to create an account using a pre-existing google account. Once you are logged in, you will have access to additional pages on the top navigation bar on the web app. The top right item in the navigation bar will be your **username**. Click the dropdown here will provide access to user preferences and logging out. Usernames are assigned automatically based on your google credentials. Please contact Neuvue development team if you'd like to change your username. Passwords are automatically managed by the google account you used to create the NeuVue account.

Regular updates to the app will be posted to the "Recent Changes" widget located on the home screen. You can continue to the next step of accessing the proofreading interface by then clicking "My Tasks" in the top navigation bar.

### Task Page

<img src="https://i.imgur.com/OWiPeYC.jpg" alt="Task Page" width="800"/>

The task page will be the central console that you will use to start proofreading on specific task types, or *namespaces*, that exist for your user. Each blue row in the task page represents a task type assigned to your user. The number in parathenses at the end of each task type name is the number of pending tasks that you are currently assigned for that task. At the right of the page, you will also find tables corresponding to each task type containing summary statistics on number of tasks done, duration, and rate.



Clicking on the blue row header for a task type will expand it to show a table with multiple tabs. Here you can inspect the details for individual tasks separated by pending tasks and closed tasks.

<img src="https://i.imgur.com/c4mUj23.png" alt="Pending Table" width="800"/>

The pending table will show tasks for that task type ordered by descending priority level. The number in the tab after "Pending" show how many pending tasks are available. The columns are described below:

* **Task ID** - The unique identifer for this task. Useful for referencing task to NeuVue admins or developers as well as for inspecting the task in the "Inspect Task" page. Click on the task ID in this table will redirect you to the "Inspect Task" page for the task ID you clicked on.
* **Seg ID** - The unique identifier for the neuron in the volume that is the primary target for this proofreading task. Seg IDs will sometimes be repeated across many tasks or even users. Seg IDs also change after edits so a seg ID listed in the task page may be outdated by the time a user opens that task. More info here.
* **Created** - EST Datetime of creation for this task.
* **Priority** - Numerical priority of this task. Higher priority means that task will be provided to the user earlier in the queue. Skipping a task reduces the task priority by 1.
* **Status** - Current status of the task. Four possible statuses: "open", "pending", "closed", "errored". Only "open" and "pending" tasks are shown in this table.
* **Times Skipped** - Counter on how many times a task has been skipped. Skipping a task reduces the priority by 1 and after a task has been skipped it can be re-assigned to another user if the particular task types allows it.

<img src="https://i.imgur.com/jumurbc.png" alt="Closed Table" width="800"/>

The closed tab is slightly different than the pending tab. This table is sorted by the "Closed Time" column. The number in the tab after "Closed" represents the total number of closed or errored tasks listed in the table. The columns are described below:

* **Task ID** - Same as pending table column.
* **Seg ID** - Same as pending table column.
* **Opened Time** - EST Datetime of when task was first opened. This opened time will represent only the first initial open status, even after task is skipped.
* **Closed Time** - EST Datetime of when task was closed.
* **Status** - Same as pending table column.
* **Tags** - Submitted notes or tags associated with this task. Tags that do not fit in the column width can be inspected by hovering your cursor over the row.

In addition to the task tables, you will also see buttons on the right side of the task type headers. These buttons are described below:

* **Start Proofreading** - This button exists for all task types with pending tasks available and assigned to you. Click this will nagivate you to the Workspace page, where the next task will automatically be queued up and displayed.
* **Add More Tasks** - Available for some task types only. Clicking this will allow additional tasks to be assigned to your user in cases where you deplete your queue or would like fresh tasks to work on. The number of tasks added to your user depends on the task type and there are certain limits set on how many tasks can be assigned to one user at a time.
* **Remove Skipped Tasks** - Available for some task types only. Clicking this will remove all tasks that have been skipped once or more from your queue permanently.

From this point you can begin proofreading by deciding on which task types you would like to work on and then clicking "Start Proofreading" for that task type. This will navigate you to the workspace page, which is the main interface for proofreading work.

## Proofreading Workspace

### Workspace Page

<img src="https://i.imgur.com/CEsxB92.jpg" alt="Workspace Page" width="800"/>

The workspace page provides all the tools necessary to complete a proofreading task. The page is an extension of [Neuroglancer](https://github.com/google/neuroglancer), the primary tool for viewing, annotating, and editing the volumetric data we use for proofreading.

The workspace page consists an embedded neuroglancer window, task-specific buttons, and a toggle-able side panel that contains information about the current task as well as additional features. Once the user navigates to the workspace, a task from the queue will automatically be loaded in and set to status *open*. If a task is already open for the selected task type, that task will be re-opened.

Neuroglancer documentation will be in a separate section. Click here for a quick explanation on how to operate Neuroglancer.

The side panel is an imporatant resource to find out the instructions of a task and important details such as segmentation ID and task ID. By default, the side panel will be expanded when a task is opened for the first time in the current session but it can be hidden by clicking the shaded area directly to the left of the side panel. The side panel also has the "Task Tags" widget, where you can add unstructured comma-separated tags to the task that will be retained on submission, as well as button to copy the current Neuroglancer state in a URL format to share with others.

The buttons on the top and bottom of the Neuroglancer window a combination of contextual operations for a task (submit, decide, annotate) and regular app functions (flag, save, skip). The latter are available for all tasks and are always at the bottom of the screen.

* **Flag Task** - Opens a confirm dialog box to flag (report) a task in case it has an issue loading properly or if there is something in the data that is preventing you from finishing the task.
* **Save State** - Saves the current Neuroglancer state to the queue so when you return to the task at a later time the Neuroglancer window resets back to the latest saved state.
* **Skip Task** - Skips the current task and automatically opens the next one if available.
* **Remove Task from Queue** - (Only available for some task types) Permanently removes the task from your queue and automatically opens the next one if available.
* **Save and Exit Task** - Saves the current Neuroglancer state and exits back to the Task page. This is the only safe way to exit a task and ensure all your progress is recorded!

For each task type, there will be various additional buttons added such as a simple green "Submit" button or multiple options such as "Yes", "No", "Unsure" that will also appear at the top or bottom of the workspace page. These buttons are typically what a user clicks to finish a task and therefore once a "submit" or decision button is clicked there is no way to return to that task unless an admin resets it for you.

The common submissions methods of task are:

* **Submit** - Simple submit button. Clicking this button will close the current task and load the next.
* **Forced Choice** - Option buttons that need to be selected for the given task to complete it.

Some forced choice tasks have both decision buttons and a "Submit" button. In these cases you must a select a decision and then click "Submit" when you are ready to submit the task. For all tasks, refer to the instructions in the side panel for more concrete detail on how and when to submit the task.

### Neuroglancer (WIP)
Here is a great instructional video on how to operate Neuroglancer for basic navigation and data exploration.

<iframe width="560" height="315" src="https://www.youtube.com/embed/TwBTyWWnbxc" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

[This cheatsheet](https://docs.google.com/document/d/1eypqJ9iI1GlWSPMTZQo9oDCLEahye6oYo_CuhS_5QTA/edit?usp=sharing) (credit to flywire.ai) has additional useful information thats specific to this proofreading effort!

## Additional Pages and Tools

NeuVue contains other tools to help proofreading or training. These are all accessible through the navigation bar at the top of any NeuVue page.

### Inspect Task

<img src="https://i.imgur.com/yDWxmXq.jpg" alt="Inspect Task Page" width="800"/>

The inspect task page has a similar layout to the workspace except it does not contain any submission or decision buttons. This page is useful to re-visit older, closed tasks or share a particular task with others. To open a task in the inspect task page, you can either copy the task ID in input box located on app.neuvue.io/inspect or click on a task ID link in the Tasks page.

### Synapse Viewer

<img src="https://i.imgur.com/a29xKER.png" alt="Synapse Viewer Page" width="800"/>

The synapse viewer page is a visualization tool which means it can be accessed by any user with a valid root ID. It displays all presynaptic and postsynaptic locations for a valid root ID or multiple IDs. The pre and post annotations for each root ID are placed in an individual Neuroglancer layer so colors and sizes can be indepedently set. The sidebar displays information of on the number of connections for each root ID. This information can be copied or downloaded with the buttons below the table in the sidebar as well. To use the synaptic viewer, copy the list of root IDs (comma-separated) you want to visualize and paste them in the input box at app.neuvue.io/synapse.

Be aware that visualizing more than 10 root IDs at a time in the synpase viewer may cause Neuroglancer or your browser to crash!

### User Preferences

<img src="https://i.imgur.com/3uVM8yo.jpg" alt="User Preferences" width="800"/>

The user preferences config is a user-specific collection of Neuroglancer settings that are applied globally to all tasks. These settings include aethetic configurations such as annotation color and opacity as well as hardware settings that can increase the performance of Neuroglancer on your system. You can access the preferences for your user account at app.neuvue.io/preferences.

Preferences are disabled by default, each individual preference must be switched "on" to take effect.

### External Neuroglancer

When a Neuroglancer link is copied from the app, it will use our externally hosted Neuroglancer instance, neuroglancer.neuvue.io. This is an identical Neuroglancer instance as the one used in NeuVue and requires no tasks or independent queue to use. Therefore, links from this neuroglancer instance can be freely distributed and shared.

## FAQ
### What Browser/OS should I use?

Any modern OS should work with NeuVue. To lower the chances of crashes or missing functionality, we recommend all users proofreading using Google Chrome. There have been compatibility issues with Safari and Firefox in the past.

### What should I do if I'm having a techical issue?

Copy the task ID and paste in the proofreading slack channel. Describe your issue in detail and paste your task ID, browser and OS as well. A NeuVue developer will then provide more specific instructions on how to troubleshoot or fix the issue.

### Can I refresh the page when I'm proofreading?

We recommend you do not refresh your browser when on the workspace page. This can cause data loss and an inaccurate record of task duration. Instead, we recommend clicking the "Save and Exit" button that should exist in the bottom right of the page.

### Is there an undo for Neuroglancer?

Yes, on the top right there will be an "undo/redo" arrow buttons that can be used to undo layer/ID selects, pans, zooms, and any changes to the Neuroglancer state. ** However, you cannot undo direct edits (i.e. splits/merges). ** To undo these, you can do the inverse operation for the undo, such as merging two accidently split IDs or splitting two accidently merged IDs.

### How do I stop Neuroglancer from lagging/slowing down?

Neuroglancer takes up a lot of system memory and CPU, so in some cases it might be better to lower the maximum amount of memory and CPU time Neuroglancer is allowed to use in the NeuVue preferences page.

For tasks that require a lot of root IDs to selected at once, we recommend unselecting IDs that are no longer being worked on or looked at.
