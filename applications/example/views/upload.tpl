<p>{{message}}</p>
<form action="{{ BASE_URL }}example/recommended/upload" method="post" enctype="multipart/form-data">
  Select a file: <input type="file" name="upload" />
  <input type="submit" value="Start upload" />
</form>
%rebase('example/',title='Upload')