This application allows a user to upload multiple files and ask questions based on their contents using OpenAI. Please is the guide to use it.

Application is deployed to Azure using Azure App Service. Can be accessed URL below,

Step 1: Go to application via link  https://ps-file-bot.azurewebsites.net/	
![image](https://github.com/m-o-w/ps-filebot/assets/11540681/76397884-054c-4e14-b07f-dd606d4d808e)

Step 2: You would need your OpenAI API key to access this. You can get your key from here -> https://platform.openai.com/account/api-keys
Step 3: Enter the API key in the box below. And lick on load key. It will display a success message if the key has been loaded
	![image](https://github.com/m-o-w/ps-filebot/assets/11540681/edb44bd5-3714-4ff5-a657-82827e3d6448)
  After click
  ![image](https://github.com/m-o-w/ps-filebot/assets/11540681/b96fb462-b79e-40f7-8aed-630ae41a8ad9)
	
Step 4: You need to upload files to set the context of the conversation. You can upload multiple files as well. They can be .txt, .pdf, .doc, .csv, .xlsx. Click on "Browse Files" or drag and drop files on the box.
	![image](https://github.com/m-o-w/ps-filebot/assets/11540681/54a06d0b-6920-4e2f-88cf-182c0889182a)
Step 5: We can now start asking questions.  Put your question in the main text box and click on "Send". Allow the application to do its thing and generate the response.
	![image](https://github.com/m-o-w/ps-filebot/assets/11540681/e77be968-25c4-465f-806f-f92f56f12b24)
	
Note: 
	1. Please delete your key after testing with the "Delete Key" button if you have uploaded the file. You can delete the uploaded file by clicking on the button with the file name, pic below,
	  ![image](https://github.com/m-o-w/ps-filebot/assets/11540681/71583a6a-274b-4fe3-bfc1-aacfa0592be2)

	2. All the files uploaded are stored in the storage space of Azure App Service and removed once deleted via application
