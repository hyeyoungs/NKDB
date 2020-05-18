<!DOCTYPE html>
<html>
<head>
<title>DB Project</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<link rel="stylesheet" type="text/css" id="stylesheet" href="./css/test1.css">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
</head>
<body>

<div class="header">
  <h2>KUBiC</h2>
</div>

<div class="search">
  searching space
  <form action = "index.php" method = "get" class ="search" id="option">
		<span class="input_res">
	    <input id="search_input" class="info" placeholder ="검색어를 입력해주세요.">
		</span>
    <span class="input_res">
			<button id="search" type ="button" onclick="">Search</button>
		</span>
  </form>
</div>
<?php
if(isset($results)){
  foreach($results as r){
    ?>
    <div class="row">
      <div class="result" id="search_result" style="background-color:#aaa;">Result</div>
    </div>
    <?php
  }
}
?>

<div class="footer">
  <p>Copyright &copy;<script>document.write(new Date().getFullYear());</script> KUBiC all rights reserved
    </p>
</div>

</body>
</html>
