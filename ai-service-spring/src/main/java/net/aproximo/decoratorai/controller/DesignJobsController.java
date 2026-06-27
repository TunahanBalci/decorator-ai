package net.aproximo.decoratorai.controller;


import jakarta.validation.Valid;
import net.aproximo.decoratorai.service.DesignJobService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/design-jobs")
public class DesignJobsController {

    private final DesignJobService designJobService;


    @GetMapping(value = "/{id}")
    public String findJobById (@RequestParam long id){

    }

    @PostMapping("")
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<String> createJob(@Valid @RequestBody Job _job){

        return ResponseEntity.ok("Job created successfully");
    }
}
